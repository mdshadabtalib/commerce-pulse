from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ValidationError
from ..core.logging import get_logger
from ..models.analytics import (
    Forecast as ForecastModel,
    ForecastMetric,
    ForecastModelType,
    ForecastRun,
    ForecastStatus,
)
from ..models.order import Order, OrderLineItem, OrderStatus
from ..schemas.analytics import (
    DateRangeFilter,
    ForecastAccuracy,
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    TimeSeriesPoint,
)
from .analytics_service import AnalyticsService

logger = get_logger(__name__)

_PAID_STATUSES = {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore

    _HAS_ETS = True
except Exception:  # pragma: no cover
    _HAS_ETS = False

try:
    from prophet import Prophet  # type: ignore

    _HAS_PROPHET = True
except Exception:  # pragma: no cover
    _HAS_PROPHET = False

try:
    from statsmodels.tsa.arima.model import ARIMA  # type: ignore

    _HAS_ARIMA = True
except Exception:  # pragma: no cover
    _HAS_ARIMA = False


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return float("inf")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def _smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    mask = denom != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100.0)


def naive_forecast(history: np.ndarray, horizon: int) -> np.ndarray:
    if len(history) == 0:
        return np.zeros(horizon)
    last = float(history[-1])
    return np.full(horizon, last)


def moving_average_forecast(history: np.ndarray, horizon: int, window: int = 14) -> np.ndarray:
    arr = np.asarray(history, dtype=float)
    if len(arr) == 0:
        return np.zeros(horizon)
    w = max(1, min(window, len(arr)))
    base = float(np.mean(arr[-w:]))
    return np.full(horizon, base)


def seasonal_naive_forecast(history: np.ndarray, horizon: int, seasonal_period: int = 7) -> np.ndarray:
    arr = np.asarray(history, dtype=float)
    if len(arr) == 0:
        return np.zeros(horizon)
    sp = max(1, seasonal_period)
    out = np.empty(horizon, dtype=float)
    n = len(arr)
    for i in range(horizon):
        idx = n - sp + (i % sp)
        out[i] = float(arr[idx]) if idx >= 0 else float(arr[-1])
    return out


def ets_forecast(history: np.ndarray, horizon: int) -> np.ndarray | None:
    if not _HAS_ETS or len(history) < 8:
        return None
    arr = np.asarray(history, dtype=float)
    try:
        seasonal = "add" if len(arr) >= 24 else None
        seasonal_periods = 7 if seasonal else None
        model = ExponentialSmoothing(
            arr,
            trend="add",
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        ).fit(optimized=True)
        fc = model.forecast(horizon)
        return np.asarray(fc, dtype=float)
    except Exception:
        return None


def arima_forecast(history: np.ndarray, horizon: int) -> np.ndarray | None:
    if not _HAS_ARIMA or len(history) < 16:
        return None
    arr = np.asarray(history, dtype=float)
    try:
        best: tuple[float, np.ndarray] | None = None
        for order in [(1, 1, 1), (0, 1, 1), (1, 1, 0), (2, 1, 0)]:
            try:
                m = ARIMA(arr, order=order).fit()
                fc = np.asarray(m.forecast(horizon), dtype=float)
                resid = np.asarray(m.resid, dtype=float)
                aic = float(m.aic) if hasattr(m, "aic") else np.nan
                score = aic if np.isfinite(aic) else _rmse(arr[len(arr) - len(resid):], arr[len(arr) - len(resid):] - resid)
                if best is None or score < best[0]:
                    best = (score, fc)
            except Exception:
                continue
        return best[1] if best else None
    except Exception:
        return None


def prophet_forecast(dates: list[datetime], values: list[float], horizon: int) -> np.ndarray | None:
    if not _HAS_PROPHET or len(dates) < 14:
        return None
    try:
        df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": values})
        m = Prophet(daily_seasonality=len(df) >= 60, weekly_seasonality=True, yearly_seasonality=len(df) >= 365)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon)
        fc = m.predict(future)
        return np.asarray(fc["yhat"].tail(horizon).values, dtype=float)
    except Exception:
        return None


class ForecastingService:
    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self.analytics = analytics_service or AnalyticsService()

    async def _build_daily_series(
        self,
        db: AsyncSession,
        organization_id: Any,
        metric: ForecastMetric,
        date_range: DateRangeFilter | None,
    ) -> tuple[list[datetime], list[float]]:
        if metric == ForecastMetric.REVENUE:
            col = func.coalesce(func.sum(Order.total_amount), 0)
        elif metric == ForecastMetric.ORDERS:
            col = func.count(distinct(Order.id))
        elif metric == ForecastMetric.UNITS_SOLD:
            subq = (
                select(func.coalesce(func.sum(OrderLineItem.quantity), 0))
                .where(
                    OrderLineItem.organization_id == organization_id,
                    OrderLineItem.order_id == Order.id,
                )
                .correlate(Order)
                .scalar_subquery()
            )
            col = func.coalesce(subq, 0)
        else:
            raise ValidationError(f"Unsupported metric: {metric}")

        base_q = (
            select(
                func.date_trunc("day", Order.order_date).label("d"),
                col.label("v"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.status.in_(_PAID_STATUSES),
            )
        )
        if date_range:
            if date_range.start_date:
                base_q = base_q.where(Order.order_date >= datetime.combine(date_range.start_date, datetime.min.time()))
            if date_range.end_date:
                base_q = base_q.where(Order.order_date <= datetime.combine(date_range.end_date, datetime.max.time()))
        base_q = base_q.group_by("d").order_by("d")
        res = await db.execute(base_q)
        rows = res.all()
        dates: list[datetime] = []
        values: list[float] = []
        for d, v in rows:
            dt = d if isinstance(d, datetime) else datetime.combine(d, datetime.min.time())
            dates.append(dt)
            values.append(_safe_float(v))

        if dates:
            full_idx = pd.date_range(dates[0].date(), dates[-1].date(), freq="D")
            s = pd.Series(values, index=pd.DatetimeIndex([pd.Timestamp(d.date()) for d in dates]))
            s = s.reindex(full_idx, fill_value=0.0)
            return [d.to_pydatetime() for d in s.index], list(s.astype(float).values)
        return dates, values

    async def generate_forecast(
        self,
        db: AsyncSession,
        organization_id: Any,
        request: ForecastRequest,
        user_id: Any | None = None,
    ) -> ForecastResponse:
        logger.info(
            "Generating forecast",
            extra={"organization_id": str(organization_id), "metric": request.metric.value},
        )
        horizon = request.horizon_days
        confidence = request.confidence_level

        dates, values = await self._build_daily_series(db, organization_id, request.metric, request.date_range)
        n = len(values)

        forecast = ForecastModel(
            organization_id=organization_id,
            metric=request.metric,
            model_used=ForecastModelType.AUTO,
            status=ForecastStatus.PENDING,
            horizon_days=horizon,
            confidence_level=confidence,
            created_by_id=user_id,
        )
        db.add(forecast)
        await db.flush()

        if n < 14:
            forecast.status = ForecastStatus.FAILED
            forecast.error_message = (
                f"Insufficient historical data: found {n} daily points, require at least 14."
            )
            await db.commit()
            await db.refresh(forecast)
            actual_points = [
                TimeSeriesPoint(date=d, value=round(v, 2), label=request.metric.value)
                for d, v in zip(dates, values)
            ]
            return ForecastResponse(
                id=forecast.id,
                metric=forecast.metric,
                model_used=forecast.model_used,
                horizon_days=horizon,
                points=[],
                actual_points=actual_points,
                accuracy=None,
                training_period=request.date_range,
                validation_period=None,
                status=ForecastStatus.FAILED,
                created_at=forecast.created_at,
                completed_at=None,
            )

        forecast.status = ForecastStatus.TRAINING
        await db.flush()

        split = int(n * 0.8)
        train_dates, test_dates = dates[:split], dates[split:]
        train_values = np.asarray(values[:split], dtype=float)
        test_values = np.asarray(values[split:], dtype=float)
        test_len = max(1, len(test_values))

        training_period = None
        if train_dates:
            training_period = DateRangeFilter(
                start_date=train_dates[0].date(),
                end_date=train_dates[-1].date(),
            )
        validation_period = None
        if test_dates:
            validation_period = DateRangeFilter(
                start_date=test_dates[0].date(),
                end_date=test_dates[-1].date(),
            )
        forecast.training_start = train_dates[0] if train_dates else None
        forecast.training_end = train_dates[-1] if train_dates else None
        forecast.validation_start = test_dates[0] if test_dates else None
        forecast.validation_end = test_dates[-1] if test_dates else None

        candidates: list[tuple[ForecastModelType, np.ndarray, np.ndarray]] = []

        naive_val = naive_forecast(train_values, test_len)
        naive_full = naive_forecast(np.asarray(values, dtype=float), horizon)
        candidates.append((ForecastModelType.NAIVE, naive_val, naive_full))

        for w in (7, 14, 30):
            if len(train_values) >= w:
                ma_val = moving_average_forecast(train_values, test_len, window=w)
                ma_full = moving_average_forecast(np.asarray(values, dtype=float), horizon, window=w)
                candidates.append((ForecastModelType.MOVING_AVERAGE, ma_val, ma_full))

        sn_val = seasonal_naive_forecast(train_values, test_len, seasonal_period=7)
        sn_full = seasonal_naive_forecast(np.asarray(values, dtype=float), horizon, seasonal_period=7)
        candidates.append((ForecastModelType.SEASONAL_NAIVE, sn_val, sn_full))

        ets_val_pred = ets_forecast(train_values, test_len)
        if ets_val_pred is not None:
            ets_full = ets_forecast(np.asarray(values, dtype=float), horizon)
            if ets_full is not None:
                candidates.append((ForecastModelType.ETS, ets_val_pred, ets_full))

        arima_val_pred = arima_forecast(train_values, test_len)
        if arima_val_pred is not None:
            arima_full = arima_forecast(np.asarray(values, dtype=float), horizon)
            if arima_full is not None:
                candidates.append((ForecastModelType.ARIMA, arima_val_pred, arima_full))

        prophet_val = prophet_forecast(train_dates, list(train_values), test_len)
        if prophet_val is not None and len(prophet_val) == test_len:
            prophet_full = prophet_forecast(dates, values, horizon)
            if prophet_full is not None and len(prophet_full) == horizon:
                candidates.append((ForecastModelType.PROPHET, prophet_val, prophet_full))

        best: tuple[float, ForecastModelType, np.ndarray, np.ndarray] | None = None
        runs_info: list[tuple[ForecastModelType, float, float, float, float, bool]] = []

        for model_type, val_pred, full_pred in candidates:
            if len(val_pred) != test_len:
                continue
            val_pred_clipped = np.clip(val_pred, 0, None)
            test_clipped = np.clip(test_values, 0, None)
            rmse = _rmse(test_clipped, val_pred_clipped)
            mape_v = _mape(test_clipped, val_pred_clipped)
            mae_v = _mae(test_clipped, val_pred_clipped)
            smape_v = _smape(test_clipped, val_pred_clipped)
            score = rmse
            selected = False
            if best is None or score < best[0]:
                if best is not None:
                    runs_info.append((best[1], best[2], best[3], best[4], best[5], False))
                best = (score, model_type, rmse, mape_v, mae_v, smape_v)
                selected = True
            else:
                runs_info.append((model_type, rmse, mape_v, mae_v, smape_v, False))

        if best is None:
            forecast.status = ForecastStatus.FAILED
            forecast.error_message = "No forecasting candidates produced valid output."
            await db.commit()
            await db.refresh(forecast)
            actual_points = [
                TimeSeriesPoint(date=d, value=round(v, 2), label=request.metric.value)
                for d, v in zip(dates, values)
            ]
            return ForecastResponse(
                id=forecast.id,
                metric=forecast.metric,
                model_used=ForecastModelType.AUTO,
                horizon_days=horizon,
                points=[],
                actual_points=actual_points,
                accuracy=None,
                training_period=training_period,
                validation_period=validation_period,
                status=ForecastStatus.FAILED,
                created_at=forecast.created_at,
                completed_at=None,
            )

        best_score, best_model, best_rmse, best_mape, best_mae, best_smape = best
        runs_info.append((best_model, best_rmse, best_mape, best_mae, best_smape, True))

        selected_candidate = next((c for c in candidates if c[0] == best_model), candidates[0])
        best_val_pred = selected_candidate[1]
        best_full_pred = selected_candidate[2]

        resid = np.asarray(test_values, dtype=float) - np.asarray(best_val_pred, dtype=float)
        std_resid = float(np.std(resid, ddof=1)) if len(resid) > 1 else 0.0
        z_mult = float(stats.norm.ppf(1 - (1 - confidence) / 2)) if 0 < confidence < 1 else 1.96

        start_forecast_date = (dates[-1].date() if dates else date.today()) + timedelta(days=1)
        forecast_dates = [start_forecast_date + timedelta(days=i) for i in range(horizon)]
        fc_values = np.clip(np.asarray(best_full_pred, dtype=float), 0, None)

        points: list[ForecastPoint] = []
        for i, d in enumerate(forecast_dates):
            v = float(fc_values[i])
            half_width = z_mult * std_resid
            lower = max(0.0, v - half_width)
            upper = v + half_width
            points.append(
                ForecastPoint(
                    date=d,
                    forecast_value=round(v, 2),
                    lower=round(lower, 2),
                    upper=round(upper, 2),
                )
            )

        for model_type, rmse_v, mape_v, mae_v, smape_v, was_selected in runs_info:
            run = ForecastRun(
                organization_id=organization_id,
                forecast_id=forecast.id,
                model_type=model_type,
                train_points=len(train_values),
                test_points=test_len,
                mae=round(mae_v, 4) if np.isfinite(mae_v) else None,
                rmse=round(rmse_v, 4) if np.isfinite(rmse_v) else None,
                mape=round(mape_v, 4) if np.isfinite(mape_v) else None,
                smape=round(smape_v, 4) if np.isfinite(smape_v) else None,
                was_selected=was_selected,
            )
            db.add(run)

        forecast.model_used = best_model
        forecast.status = ForecastStatus.COMPLETED
        forecast.points = [p.model_dump() for p in points]
        forecast.actual_points = [
            {"date": d.isoformat(), "value": round(v, 2), "label": request.metric.value}
            for d, v in zip(dates, values)
        ]
        forecast.mae = round(best_mae, 4) if np.isfinite(best_mae) else None
        forecast.rmse = round(best_rmse, 4) if np.isfinite(best_rmse) else None
        forecast.mape = round(best_mape, 4) if np.isfinite(best_mape) else None
        forecast.smape = round(best_smape, 4) if np.isfinite(best_smape) else None
        forecast.residuals_std = round(std_resid, 4) if np.isfinite(std_resid) else None
        forecast.completed_at = datetime.now()

        await db.commit()
        await db.refresh(forecast)

        actual_points_out = [
            TimeSeriesPoint(date=d, value=round(v, 2), label=request.metric.value)
            for d, v in zip(dates, values)
        ]

        accuracy = ForecastAccuracy(
            MAE=round(best_mae, 4) if np.isfinite(best_mae) else None,
            RMSE=round(best_rmse, 4) if np.isfinite(best_rmse) else None,
            MAPE=round(best_mape, 4) if np.isfinite(best_mape) else None,
            SMAPE=round(best_smape, 4) if np.isfinite(best_smape) else None,
        )

        return ForecastResponse(
            id=forecast.id,
            metric=forecast.metric,
            model_used=forecast.model_used,
            horizon_days=forecast.horizon_days,
            points=points,
            actual_points=actual_points_out,
            accuracy=accuracy,
            training_period=training_period,
            validation_period=validation_period,
            status=forecast.status,
            created_at=forecast.created_at,
            completed_at=forecast.completed_at,
        )

    async def get_forecast_history(
        self,
        db: AsyncSession,
        organization_id: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ForecastResponse]:
        logger.info("Retrieving forecast history", extra={"organization_id": str(organization_id)})
        q = (
            select(ForecastModel)
            .where(ForecastModel.organization_id == organization_id)
            .order_by(ForecastModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(q)
        rows = res.scalars().all()

        out: list[ForecastResponse] = []
        for fc in rows:
            points: list[ForecastPoint] = []
            for p in fc.points or []:
                try:
                    d = p.get("date")
                    if isinstance(d, str):
                        d = pd.to_datetime(d).date()
                    points.append(
                        ForecastPoint(
                            date=d,
                            forecast_value=float(p.get("forecast_value", 0)),
                            lower=float(p.get("lower", 0)),
                            upper=float(p.get("upper", 0)),
                        )
                    )
                except Exception:
                    continue

            actual: list[TimeSeriesPoint] = []
            for ap in fc.actual_points or []:
                try:
                    d = ap.get("date")
                    if isinstance(d, str):
                        d = pd.to_datetime(d).to_pydatetime()
                    actual.append(
                        TimeSeriesPoint(
                            date=d,
                            value=float(ap.get("value", 0)),
                            label=ap.get("label"),
                        )
                    )
                except Exception:
                    continue

            training_period = None
            if fc.training_start and fc.training_end:
                training_period = DateRangeFilter(
                    start_date=fc.training_start.date(),
                    end_date=fc.training_end.date(),
                )
            validation_period = None
            if fc.validation_start and fc.validation_end:
                validation_period = DateRangeFilter(
                    start_date=fc.validation_start.date(),
                    end_date=fc.validation_end.date(),
                )

            accuracy = None
            if fc.mae or fc.rmse or fc.mape:
                accuracy = ForecastAccuracy(
                    MAE=_safe_float(fc.mae),
                    RMSE=_safe_float(fc.rmse),
                    MAPE=_safe_float(fc.mape),
                    SMAPE=_safe_float(fc.smape),
                )

            out.append(
                ForecastResponse(
                    id=fc.id,
                    metric=fc.metric,
                    model_used=fc.model_used,
                    horizon_days=fc.horizon_days,
                    points=points,
                    actual_points=actual,
                    accuracy=accuracy,
                    training_period=training_period,
                    validation_period=validation_period,
                    status=fc.status,
                    created_at=fc.created_at,
                    completed_at=fc.completed_at,
                )
            )
        return out
