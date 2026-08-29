from __future__ import annotations

from typing import Any, Optional

from kombu import Queue

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

celery_app: Optional[Any] = None

try:
    from celery import Celery
    from kombu import Exchange

    celery_app = Celery(
        "commerce_pulse",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    default_exchange = Exchange("default", type="direct")
    emails_exchange = Exchange("emails", type="direct")
    imports_exchange = Exchange("imports", type="direct")
    forecasts_exchange = Exchange("forecasts", type="direct")
    reports_exchange = Exchange("reports", type="direct")

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_eager_propagates=True,
        task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
        task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
        task_default_queue="default",
        task_queues=[
            Queue(
                "default",
                exchange=default_exchange,
                routing_key="default",
            ),
            Queue(
                "emails",
                exchange=emails_exchange,
                routing_key="emails.#",
            ),
            Queue(
                "imports",
                exchange=imports_exchange,
                routing_key="imports.#",
            ),
            Queue(
                "forecasts",
                exchange=forecasts_exchange,
                routing_key="forecasts.#",
            ),
            Queue(
                "reports",
                exchange=reports_exchange,
                routing_key="reports.#",
            ),
        ],
        task_routes={
            "emails.*": {"queue": "emails"},
            "imports.*": {"queue": "imports"},
            "forecasts.*": {"queue": "forecasts"},
            "reports.*": {"queue": "reports"},
        },
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_track_started=True,
        task_store_errors_even_if_ignored=True,
        result_expires=86400,
    )

    celery_app.autodiscover_tasks(
        [
            "app.tasks",
            "app.tasks.emails",
            "app.tasks.imports",
            "app.tasks.forecasts",
            "app.tasks.reports",
        ],
        force=False,
    )

    logger.info(
        "Celery app initialized.",
        extra={
            "broker": settings.CELERY_BROKER_URL,
            "queues": ["default", "emails", "imports", "forecasts", "reports"],
        },
    )

except ImportError as exc:
    logger.warning(
        "Celery not available; background tasks will use eager fallback.",
        extra={"error": str(exc)},
    )
    celery_app = None
except Exception as exc:
    logger.warning(
        "Failed to initialize Celery; background tasks disabled.",
        extra={"error": str(exc)},
    )
    celery_app = None
