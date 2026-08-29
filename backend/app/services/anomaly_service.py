from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import NotFoundError, ValidationError
from ..core.logging import get_logger
from ..models.analytics import Anomaly as AnomalyModel
from ..models.order import Order, OrderLineItem, OrderStatus, Refund
from ..schemas.analytics import AnomalyResponse, AnomalySeverity, AnomalyStatus
from ..schemas.common import DateRangeFilter


class AnomalyType:
    """Simple namespace for anomaly type strings — stored as plain strings in the DB."""
    SPIKE = "SPIKE"
    DROP = "DROP"
    OUTLIER = "OUTLIER"
    TREND_BREAK = "TREND_BREAK"
    SEASONALITY = "SEASONALITY"

logger = get_logger(__name__)

_PAID_STATUSES = {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _zscore(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    mu = np.nanmean(arr)
    sigma = np.nanstd(arr, ddof=1)
    if not np.isfinite(sigma) or sigma == 0:
        return np.zeros_like(arr)
    return (arr - mu) / sigma


def _mad(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    med = np.nanmedian(arr)
    mad = np.nanmedian(np.abs(arr - med))
    if not np.isfinite(mad) or mad == 0:
        return np.zeros_like(arr)
    modified_z = 0.6745 * (arr - med) / mad
    return modified_z


def _iqr_bounds(values: np.ndarray) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    q1 = np.nanpercentile(arr, 25)
    q3 = np.nanpercentile(arr, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return float(lower), float(upper)


def _classify_severity(z_abs: float, pct_change: float) -> AnomalySeverity:
    if z_abs > 5 or abs(pct_change) > 50:
        return AnomalySeverity.HIGH
    if z_abs > 3 or abs(pct_change) > 25:
        return AnomalySeverity.MEDIUM
    return AnomalySeverity.LOW


class AnomalyService:
    async def _get_daily_metric_series(
        self,
        db: AsyncSession,
        organization_id: Any,
        metric: str,
        lookback_days: int,
    ) -> tuple[list[datetime], list[float]]:
        end = datetime.now()
        start = end - timedelta(days=lookback_days)

        if metric == "revenue":
            value_expr = func.coalesce(func.sum(Order.total_amount), 0)
            q = (
                select(func.date_trunc("day", Order.order_date).label("d"), value_expr.label("v"))
                .where(
                    Order.organization_id == organization_id,
                    Order.status.in_(_PAID_STATUSES),
                    Order.order_date >= start,
                    Order.order_date <= end,
                )
                .group_by("d")
                .order_by("d")
            )
        elif metric == "orders":
            value_expr = func.count(distinct(Order.id))
            q = (
                select(func.date_trunc("day", Order.order_date).label("d"), value_expr.label("v"))
                .where(
                    Order.organization_id == organization_id,
                    Order.status.in_(_PAID_STATUSES),
                    Order.order_date >= start,
                    Order.order_date <= end,
                )
                .group_by("d")
                .order_by("d")
            )
        elif metric == "refunds":
            value_expr = func.coalesce(func.sum(Refund.amount), 0)
            q = (
                select(
                    func.date_trunc("day", Refund.processed_at).label("d"),
                    value_expr.label("v"),
                )
                .where(
                    Refund.organization_id == organization_id,
                    Refund.processed_at.isnot(None),
                    Refund.processed_at >= start,
                    Refund.processed_at <= end,
                )
                .group_by("d")
                .order_by("d")
            )
        elif metric == "units":
            q = (
                select(
                    func.date_trunc("day", Order.order_date).label("d"),
                    func.coalesce(func.sum(OrderLineItem.quantity), 0).label("v"),
                )
                .select_from(OrderLineItem)
                .join(Order, Order.id == OrderLineItem.order_id)
                .where(
                    OrderLineItem.organization_id == organization_id,
                    Order.status.in_(_PAID_STATUSES),
                    Order.order_date >= start,
                    Order.order_date <= end,
                )
                .group_by("d")
                .order_by("d")
            )
        else:
            raise ValidationError(f"Unsupported anomaly metric: {metric}")

        res = await db.execute(q)
        rows = res.all()
        sparse_dates = [r[0] if isinstance(r[0], datetime) else datetime.combine(r[0], datetime.min.time()) for r in rows]
        sparse_values = [_safe_float(r[1]) for r in rows]

        if not sparse_dates:
            return [], []

        full_idx = pd.date_range(sparse_dates[0].date(), sparse_dates[-1].date(), freq="D")
        s = pd.Series(
            sparse_values,
            index=pd.DatetimeIndex([pd.Timestamp(d.date()) for d in sparse_dates]),
        )
        s = s.reindex(full_idx, fill_value=0.0)
        return [d.to_pydatetime() for d in s.index], list(s.astype(float).values)

    def _detect_univariate(
        self,
        dates: list[datetime],
        values: list[float],
        metric: str,
        sensitivity: float,
    ) -> list[dict[str, Any]]:
        if len(values) < 7:
            return []
        arr = np.asarray(values, dtype=float)
        z = np.abs(_zscore(arr))
        mz = np.abs(_mad(arr))
        lower, upper = _iqr_bounds(arr)
        iqr_flag = (arr < lower) | (arr > upper)

        mu = float(np.nanmean(arr))
        med = float(np.nanmedian(arr))

        detected: list[dict[str, Any]] = []
        for i in range(len(arr)):
            methods: list[str] = []
            if z[i] >= sensitivity:
                methods.append("z-score")
            if mz[i] >= sensitivity:
                methods.append("MAD")
            if iqr_flag[i]:
                methods.append("IQR")
            if not methods:
                continue
            actual = float(arr[i])
            expected = med if methods.count("MAD") else mu
            deviation = actual - expected
            pct_change = (deviation / expected * 100.0) if expected not in (0, 0.0) else (0.0 if actual == 0 else float("inf"))
            max_z = max(z[i], mz[i])
            severity = _classify_severity(float(max_z), pct_change if np.isfinite(pct_change) else 0.0)
            anomaly_type = AnomalyType.SPIKE if actual > expected else AnomalyType.DROP
            explanation_parts = []
            if "z-score" in methods:
                explanation_parts.append(f"Z-score={z[i]:.2f}")
            if "MAD" in methods:
                explanation_parts.append(f"Modified Z={mz[i]:.2f}")
            if "IQR" in methods:
                explanation_parts.append(f"Outside IQR bounds [{lower:.2f},{upper:.2f}]")
            explanation = (
                f"{metric.capitalize()} anomaly on {dates[i].date()}: "
                f"actual={actual:.2f}, expected~{expected:.2f} ({'+' if deviation >= 0 else ''}{deviation:.2f}, "
                f"{('+' if pct_change >= 0 else '') + (f'{pct_change:.1f}' if np.isfinite(pct_change) else 'N/A')}%). "
                f"Detected via: {', '.join(methods)}."
            )
            detected.append(
                {
                    "metric": metric,
                    "timestamp": dates[i],
                    "value": actual,
                    "expected_value": expected,
                    "deviation": deviation,
                    "deviation_percentage": float(pct_change) if np.isfinite(pct_change) else None,
                    "severity": severity,
                    "anomaly_type": anomaly_type,
                    "detection_method": "+".join(methods),
                    "explanation": explanation,
                    "evidence": {
                        "z_score": round(float(z[i]), 4),
                        "modified_z": round(float(mz[i]), 4),
                        "iqr_lower": round(lower, 4),
                        "iqr_upper": round(upper, 4),
                        "mean": round(mu, 4),
                        "median": round(med, 4),
                        "methods": methods,
                    },
                }
            )
        return detected

    async def detect_anomalies(
        self,
        db: AsyncSession,
        organization_id: Any,
        lookback_days: int = 90,
        sensitivity: float | None = None,
        persist: bool = True,
    ) -> list[AnomalyResponse]:
        sensitivity = sensitivity if sensitivity is not None else settings.ANOMALY_DETECTION_SENSITIVITY
        logger.info(
            "Running anomaly detection",
            extra={
                "organization_id": str(organization_id),
                "lookback_days": lookback_days,
                "sensitivity": sensitivity,
            },
        )
        metrics = ["revenue", "orders", "refunds", "units"]
        all_detected: list[dict[str, Any]] = []

        for metric in metrics:
            try:
                dates, values = await self._get_daily_metric_series(db, organization_id, metric, lookback_days)
                detections = self._detect_univariate(dates, values, metric, sensitivity)
                all_detected.extend(detections)
            except Exception as exc:
                logger.warning(
                    "Anomaly detection failed for metric",
                    exc_info=True,
                    extra={"metric": metric, "error": str(exc)},
                )

        existing_sigs: set[tuple[str, datetime]] = set()
        if persist:
            end = datetime.now()
            start = end - timedelta(days=lookback_days + 1)
            existing_q = select(AnomalyModel.metric, AnomalyModel.detected_at).where(
                AnomalyModel.organization_id == organization_id,
                AnomalyModel.detected_at >= start,
                AnomalyModel.detected_at <= end,
            )
            existing_res = await db.execute(existing_q)
            for m, ts in existing_res.all():
                ts_dt = ts if isinstance(ts, datetime) else datetime.combine(ts, datetime.min.time())
                existing_sigs.add((m, ts_dt.replace(hour=0, minute=0, second=0, microsecond=0)))

        stored_models: list[AnomalyModel] = []
        for det in all_detected:
            ts = det["timestamp"]
            key = (det["metric"], ts.replace(hour=0, minute=0, second=0, microsecond=0))
            if key in existing_sigs:
                continue
            if persist:
                model = AnomalyModel(
                    organization_id=organization_id,
                    metric=det["metric"],
                    anomaly_type=det["anomaly_type"],
                    severity=det["severity"],
                    status=AnomalyStatus.DETECTED,
                    detected_at=det["timestamp"],
                    value=det["value"],
                    expected_value=det["expected_value"],
                    deviation=det["deviation"],
                    deviation_percentage=det["deviation_percentage"],
                    detection_method=det["detection_method"],
                    description=det["explanation"],
                    evidence=det["evidence"],
                )
                db.add(model)
                stored_models.append(model)
                existing_sigs.add(key)

        if persist:
            await db.flush()

        results: list[AnomalyResponse] = []
        for m, det in zip(stored_models, all_detected[-len(stored_models):]) if stored_models else zip([], []):
            results.append(self._model_to_response(m))

        if not results and stored_models:
            for m in stored_models:
                results.append(self._model_to_response(m))

        if not results:
            q = (
                select(AnomalyModel)
                .where(
                    AnomalyModel.organization_id == organization_id,
                    AnomalyModel.detected_at >= (datetime.now() - timedelta(days=lookback_days)),
                )
                .order_by(AnomalyModel.severity.desc(), AnomalyModel.detected_at.desc())
            )
            res = await db.execute(q)
            for m in res.scalars().all():
                results.append(self._model_to_response(m))

        if persist:
            await db.commit()
        return results

    def _model_to_response(self, m: AnomalyModel) -> AnomalyResponse:
        return AnomalyResponse(
            id=m.id,
            organization_id=m.organization_id,
            dataset_id=m.dataset_id,
            metric=m.metric,
            anomaly_type=m.anomaly_type.value if hasattr(m.anomaly_type, "value") else str(m.anomaly_type),
            severity=m.severity,
            status=m.status,
            detected_at=m.detected_at,
            value=float(m.value),
            expected_value=float(m.expected_value) if m.expected_value is not None else None,
            deviation=float(m.deviation) if m.deviation is not None else None,
            deviation_percentage=float(m.deviation_percentage) if m.deviation_percentage is not None else None,
            description=m.description,
            evidence=m.evidence,
            metadata=m.metadata,
            acknowledged_by=m.acknowledged_by_id,
            acknowledged_at=m.acknowledged_at,
            resolved_by=m.resolved_by_id,
            resolved_at=m.resolved_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def acknowledge_anomaly(
        self,
        db: AsyncSession,
        anomaly_id: Any,
        user_id: Any,
    ) -> AnomalyResponse:
        q = select(AnomalyModel).where(AnomalyModel.id == anomaly_id)
        res = await db.execute(q)
        model = res.scalar_one_or_none()
        if model is None:
            raise NotFoundError(f"Anomaly {anomaly_id} not found")
        model.status = AnomalyStatus.ACKNOWLEDGED
        model.acknowledged_by_id = user_id
        model.acknowledged_at = datetime.now()
        await db.commit()
        await db.refresh(model)
        return self._model_to_response(model)

    async def resolve_anomaly(
        self,
        db: AsyncSession,
        anomaly_id: Any,
        user_id: Any,
        resolution_notes: str | None = None,
        mark_false_positive: bool = False,
    ) -> AnomalyResponse:
        q = select(AnomalyModel).where(AnomalyModel.id == anomaly_id)
        res = await db.execute(q)
        model = res.scalar_one_or_none()
        if model is None:
            raise NotFoundError(f"Anomaly {anomaly_id} not found")
        model.status = AnomalyStatus.FALSE_POSITIVE if mark_false_positive else AnomalyStatus.RESOLVED
        model.resolved_by_id = user_id
        model.resolved_at = datetime.now()
        if resolution_notes:
            model.resolution_notes = resolution_notes
        await db.commit()
        await db.refresh(model)
        return self._model_to_response(model)

    async def list_anomalies(
        self,
        db: AsyncSession,
        organization_id: Any,
        status: AnomalyStatus | None = None,
        severity: AnomalySeverity | None = None,
        metric: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnomalyResponse]:
        q = select(AnomalyModel).where(AnomalyModel.organization_id == organization_id)
        if status:
            q = q.where(AnomalyModel.status == status)
        if severity:
            q = q.where(AnomalyModel.severity == severity)
        if metric:
            q = q.where(AnomalyModel.metric == metric)
        q = q.order_by(AnomalyModel.detected_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        return [self._model_to_response(m) for m in res.scalars().all()]
