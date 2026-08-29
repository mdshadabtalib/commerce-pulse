"""Forecast generation Celery tasks."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from ..core.celery_app import celery_app
from ..core.logging import get_logger

logger = get_logger(__name__)

if celery_app is None:
    class _DummyCelery:
        @staticmethod
        def task(*args: Any, **kwargs: Any):
            def decorator(fn):
                return fn
            return decorator
    celery_app = _DummyCelery()  # type: ignore[assignment]


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


@celery_app.task(  # type: ignore[attr-defined]
    name="forecasts.generate",
    bind=True,
    max_retries=1,
    queue="forecasts",
    acks_late=True,
    time_limit=1800,
    soft_time_limit=1700,
)
def generate_forecast(
    self: Any,
    forecast_id: str,
    org_id: str,
    metric: str,
    horizon_days: int,
    model_type: str = "AUTO",
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    """Train and generate a sales forecast for the given metric and horizon.

    Updates the Forecast and ForecastRun records on completion.

    Args:
        forecast_id: UUID of the Forecast record.
        org_id: UUID of the organization.
        metric: ForecastMetric value (REVENUE/ORDERS/UNITS_SOLD).
        horizon_days: Number of days to forecast ahead.
        model_type: ForecastModelType or AUTO for auto-selection.
        confidence_level: Confidence interval width (0.5–0.99).
    """
    async def _run() -> dict[str, Any]:
        from ..db.session import async_session_factory
        from ..services.forecasting_service import ForecastingService
        from ..schemas.analytics import ForecastMetric, ForecastModelType

        svc = ForecastingService()

        try:
            metric_enum = ForecastMetric(metric)
        except ValueError:
            raise ValueError(f"Invalid forecast metric: {metric}")

        try:
            model_enum = ForecastModelType(model_type)
        except ValueError:
            model_enum = ForecastModelType.AUTO

        async with async_session_factory() as db:
            try:
                result = await svc.generate_forecast(
                    db,
                    organization_id=UUID(org_id),
                    metric=metric_enum,
                    horizon_days=horizon_days,
                    model_type=model_enum,
                    confidence_level=confidence_level,
                    forecast_id=UUID(forecast_id),
                )
                await db.commit()
                return {"forecast_id": forecast_id, "status": "completed", "model_used": result.model_used}
            except Exception as exc:
                await db.rollback()
                # Mark forecast as failed
                try:
                    from sqlalchemy import select
                    from ..models.analytics import Forecast
                    from datetime import datetime, timezone
                    async with async_session_factory() as err_db:
                        r = await err_db.execute(select(Forecast).where(Forecast.id == UUID(forecast_id)))
                        forecast = r.scalar_one_or_none()
                        if forecast:
                            forecast.status = "FAILED"
                            err_db.add(forecast)
                            await err_db.commit()
                except Exception:
                    pass
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("Forecast generation failed.", extra={"forecast_id": forecast_id, "error": str(exc)})
        raise self.retry(exc=exc)


@celery_app.task(  # type: ignore[attr-defined]
    name="forecasts.detect_anomalies",
    bind=True,
    max_retries=2,
    queue="forecasts",
    acks_late=True,
    time_limit=600,
)
def detect_anomalies(
    self: Any,
    org_id: str,
    days_back: int = 30,
) -> dict[str, Any]:
    """Run anomaly detection for all metrics for an organization."""
    async def _run() -> dict[str, Any]:
        from ..db.session import async_session_factory
        from ..services.anomaly_service import AnomalyService
        from ..schemas.common import DateRangeFilter
        from datetime import date, timedelta

        svc = AnomalyService()
        end = date.today()
        start = end - timedelta(days=days_back)

        async with async_session_factory() as db:
            anomalies = await svc.detect_anomalies(
                db,
                organization_id=UUID(org_id),
                date_range=DateRangeFilter(start_date=start, end_date=end),
            )
            await db.commit()
            return {"org_id": org_id, "anomalies_detected": len(anomalies)}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("Anomaly detection failed.", extra={"org_id": org_id, "error": str(exc)})
        raise self.retry(exc=exc)
