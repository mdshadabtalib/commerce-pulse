from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings
from ..core.errors import DatabaseError, ServiceUnavailableError
from ..core.logging import get_logger

logger = get_logger(__name__)


def _build_engine_from_url(database_url: str, *, pool_size: int = 20, max_overflow: int = 10, **kwargs: object) -> AsyncEngine:
    connect_args: dict[str, object] = {}
    if "+asyncpg" in database_url:
        connect_args = {
            "server_settings": {
                "jit": "off",
                "application_name": settings.APP_NAME,
                "timezone": settings.DEFAULT_TIMEZONE,
            },
            "command_timeout": 30,
        }
    engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=pool_size,
        max_overflow=max_overflow,
        future=True,
        echo=False,
        echo_pool=False,
        connect_args=connect_args,
        execution_options={
            "isolation_level": "READ COMMITTED",
        },
        **kwargs,
    )
    return engine


def _build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


_engine: Optional[AsyncEngine] = None
async_session_factory: async_sessionmaker[AsyncSession]


def initialize_db(
    *,
    database_url: Optional[str] = None,
    pool_size: int = 20,
    max_overflow: int = 10,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global _engine, async_session_factory
    url = database_url or settings.DATABASE_URL
    try:
        _engine = _build_engine_from_url(url, pool_size=pool_size, max_overflow=max_overflow)
        async_session_factory = _build_session_factory(_engine)
        logger.info(
            "Database engine initialized.",
            extra={"pool_size": pool_size, "max_overflow": max_overflow},
        )
        return _engine, async_session_factory
    except Exception as exc:
        logger.critical("Failed to initialize database engine: %s", exc)
        raise ServiceUnavailableError(
            message="Failed to connect to database. Please try again later.",
        ) from exc


async def verify_db_connection() -> None:
    if _engine is None:
        raise DatabaseError(message="Database engine has not been initialized.")
    try:
        async with _engine.connect() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
            await conn.commit()
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", exc)
        raise DatabaseError(message="Database connectivity check failed.") from exc


def get_engine() -> AsyncEngine:
    if _engine is None:
        return initialize_db()[0]
    return _engine


async def shutdown_db() -> None:
    global _engine
    if _engine is not None:
        try:
            await _engine.dispose()
            logger.info("Database engine disposed successfully.")
        except Exception as exc:
            logger.warning("Error while disposing database engine: %s", exc)
        finally:
            _engine = None


def get_sync_database_url() -> str:
    return settings.DATABASE_URL_SYNC or settings.DATABASE_URL
