from __future__ import annotations

import logging
import platform
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.errors import (
    ErrorHandlerRegistry,
    RateLimitExceededError,
    RequestIdMiddleware,
    format_error_response,
    get_request_id,
)
from .core.logging import configure_logging, get_logger
from .core.security import build_rate_limiter
from .db.session import initialize_db, shutdown_db, verify_db_connection

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: float
    uptime_seconds: float


class ReadyResponse(HealthResponse):
    components: dict[str, Any]
    checks: dict[str, Any]


START_TIME: float = time.time()
API_VERSION: str = "1.0.0"


def _configure_sentry(app: FastAPI) -> None:
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured; skipping Sentry initialization.")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT.value,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            release=f"{settings.APP_NAME.lower()}@{API_VERSION}",
            send_default_pii=False,
            integrations=[
                sentry_logging,
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
        )
        app.add_middleware(SentryAsgiMiddleware)
        logger.info("Sentry integration configured successfully.")
    except Exception as exc:
        logger.warning("Failed to configure Sentry: %s. Continuing without it.", exc)


def _configure_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    cors_origins = [str(origin).rstrip("/") for origin in settings.CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=settings.CORS_ORIGINS_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Origin",
            "X-Requested-With",
            "X-Request-ID",
            "X-CSRF-Token",
            "X-Forwarded-For",
            "X-Forwarded-Proto",
            "X-Forwarded-Host",
        ],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Pagination-Total",
            "X-Pagination-Page",
            "X-Pagination-Per-Page",
            "Content-Disposition",
        ],
        max_age=600,
    )

    if settings.is_production():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],
        )

    @app.middleware("http")
    async def structured_request_logging(request: Request, call_next):
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", None)
        client_ip = request.client.host if request.client else None
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        logger.info(
            "Incoming request.",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_string": str(request.query_string),
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            status_code = response.status_code
            logger.info(
                "Request completed.",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                },
            )
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "Unhandled exception during request.",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "exc_type": type(exc).__name__,
                },
            )
            raise

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        }
        if settings.is_production():
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "script-src 'self'; "
                "connect-src 'self' https:;"
            )
        for key, value in headers.items():
            if key not in response.headers:
                response.headers[key] = value
        return response


def _build_health_router() -> APIRouter:
    router = APIRouter(tags=["Health"])

    @router.get(
        "/health",
        response_model=HealthResponse,
        summary="Service health check",
    )
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.APP_NAME,
            version=API_VERSION,
            environment=settings.ENVIRONMENT.value,
            timestamp=time.time(),
            uptime_seconds=round(time.time() - START_TIME, 3),
        )

    @router.get(
        "/ready",
        response_model=ReadyResponse,
        summary="Service readiness check",
    )
    async def ready() -> ReadyResponse:
        checks: dict[str, Any] = {}
        components: dict[str, Any] = {
            "python": {
                "version": sys.version,
                "implementation": platform.python_implementation(),
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "db_pool": "configured",
            "rate_limiter": settings.RATE_LIMIT_STORAGE,
        }

        try:
            await verify_db_connection()
            checks["database"] = {"status": "ok"}
        except Exception as exc:
            checks["database"] = {"status": "error", "error": str(exc)}

        overall = "ok"
        for check in checks.values():
            if check.get("status") != "ok":
                overall = "degraded"
                break

        return ReadyResponse(
            status=overall,
            service=settings.APP_NAME,
            version=API_VERSION,
            environment=settings.ENVIRONMENT.value,
            timestamp=time.time(),
            uptime_seconds=round(time.time() - START_TIME, 3),
            components=components,
            checks=checks,
        )

    return router


def _import_all_routers() -> dict[str, APIRouter]:
    routers: dict[str, APIRouter] = {}
    router_modules: list[tuple[str, str]] = [
        ("auth", ".routers.auth"),
        ("organizations", ".routers.organizations"),
        ("users", ".routers.users"),
        ("datasets", ".routers.datasets"),
        ("analytics", ".routers.analytics"),
        ("customers", ".routers.customers"),
        ("products", ".routers.products"),
        ("forecasting", ".routers.forecasting"),
        ("anomalies", ".routers.anomalies"),
        ("reports", ".routers.reports"),
        ("integrations", ".routers.integrations"),
        ("settings", ".routers.settings"),
    ]
    for name, module_path in router_modules:
        try:
            import importlib

            module = importlib.import_module(module_path, package=__name__.rsplit(".", 1)[0])
            router_obj = getattr(module, "router", None)
            if router_obj and isinstance(router_obj, APIRouter):
                routers[name] = router_obj
                logger.info("Loaded router: %s", name)
            else:
                logger.warning(
                    "Module %s exists but does not expose an APIRouter named 'router'. Skipping.",
                    module_path,
                )
        except ImportError as exc:
            logger.info(
                "Router module %s not yet implemented. Placeholder only. (%s)",
                module_path,
                exc,
            )
    return routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info(
        "Starting %s v%s in %s environment.",
        settings.APP_NAME,
        API_VERSION,
        settings.ENVIRONMENT.value,
    )

    try:
        initialize_db()
        logger.info("Database engine initialized during startup.")
    except Exception as exc:
        logger.critical("Database initialization failed during startup: %s", exc)
        raise

    app.state.start_time = START_TIME
    app.state.version = API_VERSION

    yield

    await shutdown_db()
    logger.info(
        "Shutdown complete for %s. Uptime: %.1fs",
        settings.APP_NAME,
        time.time() - START_TIME,
    )


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "CommercePulse Backend API - E-commerce Analytics & Insights Platform. "
            "Provides multi-tenant organization management, customer/product dataset ingestion, "
            "ML forecasting, anomaly detection, reporting and third-party integrations."
        ),
        version=API_VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs" if not settings.is_production() else None,
        redoc_url="/redoc" if not settings.is_production() else None,
        lifespan=lifespan,
        debug=settings.DEBUG,
        terms_of_service=None,
        contact={
            "name": "CommercePulse Support",
            "email": "support@commercepulse.ai",
        },
        license_info={
            "name": "Commercial",
            "identifier": "Commercial",
        },
    )

    app.state.settings = settings

    _configure_sentry(app)
    _configure_middleware(app)

    ErrorHandlerRegistry.register(app)

    limiter = build_rate_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(RateLimitExceeded)
    async def handle_ratelimit_slowapi(request: Request, exc: RateLimitExceeded):
        from fastapi.encoders import jsonable_encoder
        from fastapi.responses import JSONResponse

        request_id = get_request_id(request)
        detail = getattr(exc, "detail", None) or "Rate limit exceeded."
        retry_after = None
        for key, value in (exc.headers or {}).items():
            if "retry" in key.lower() or "reset" in key.lower():
                retry_after = value
                break
        response_body = format_error_response(
            error_code=RateLimitExceededError.error_code,
            message=str(detail),
            status_code=429,
            request_id=request_id,
            details={"retry_after": retry_after} if retry_after else None,
        )
        response = JSONResponse(status_code=429, content=jsonable_encoder(response_body))
        if retry_after:
            response.headers["Retry-After"] = str(retry_after)
        response.headers["X-Request-ID"] = request_id
        return response

    health_router = _build_health_router()
    app.include_router(health_router, prefix="", tags=["Health"])
    app.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["Health"])

    api_router = APIRouter(prefix=settings.API_V1_PREFIX)
    routers = _import_all_routers()
    for name, rtr in routers.items():
        api_router.include_router(rtr)
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        return {
            "service": settings.APP_NAME,
            "version": API_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "docs": "/docs" if not settings.is_production() else None,
            "health": "/health",
            "ready": "/ready",
            "api_prefix": settings.API_V1_PREFIX,
        }

    logger.info(
        "FastAPI application factory completed. %d router(s) registered.",
        len(routers) + 1,
    )
    return app


app = create_app()


def start_app() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development(),
        workers=1 if settings.is_development() else 4,
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    start_app()
