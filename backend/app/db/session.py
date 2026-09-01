from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings
from ..core.errors import DatabaseError, ServiceUnavailableError
from ..core.logging import get_logger

logger = get_logger(__name__)


def _is_sqlite(url: str) -> bool:
    """Return True if the database URL targets SQLite."""
    return "sqlite" in url.lower()


def _build_engine_from_url(database_url: str, *, pool_size: int = 20, max_overflow: int = 10, **kwargs: object) -> AsyncEngine:
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "future": True,
        "echo": False,
        "echo_pool": False,
    }

    if _is_sqlite(database_url):
        # SQLite does not support pool_size / max_overflow and only allows
        # SERIALIZABLE, READ UNCOMMITTED, or AUTOCOMMIT isolation levels.
        connect_args = {"check_same_thread": False}
        engine_kwargs["connect_args"] = connect_args
        engine_kwargs["execution_options"] = {
            "isolation_level": "SERIALIZABLE",
        }
    elif "+asyncpg" in database_url:
        # PostgreSQL via asyncpg
        connect_args = {
            "server_settings": {
                "jit": "off",
                "application_name": settings.APP_NAME,
                "timezone": settings.DEFAULT_TIMEZONE,
            },
            "command_timeout": 30,
        }
        engine_kwargs["pool_size"] = pool_size
        engine_kwargs["max_overflow"] = max_overflow
        engine_kwargs["pool_recycle"] = 3600
        engine_kwargs["connect_args"] = connect_args
        engine_kwargs["execution_options"] = {
            "isolation_level": "READ COMMITTED",
        }
    else:
        # Other async drivers (e.g. asyncpg, aiosqlite variant, etc.)
        engine_kwargs["pool_size"] = pool_size
        engine_kwargs["max_overflow"] = max_overflow
        engine_kwargs["pool_recycle"] = 3600
        engine_kwargs["connect_args"] = connect_args

    engine = create_async_engine(database_url, **engine_kwargs, **kwargs)
    return engine


def _build_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


_engine: Optional[AsyncEngine] = None
# Keep one factory object for the process. Router modules import this object at
# startup, while the application's lifespan binds it to the active engine.
async_session_factory: async_sessionmaker[AsyncSession] = _build_session_factory()


def _auto_create_sqlite_tables(engine: AsyncEngine) -> None:
    """Create all tables automatically when using SQLite (local dev)."""
    from sqlalchemy import create_engine

    sync_url = str(engine.url).replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False})

    from .base import Base  # noqa: F811 – import all model metadata
    # Ensure every model module is loaded so Base.metadata contains all tables.
    from ..models import (  # noqa: F401
        analytics, customer, dataset, order, organization, product, user,
    )

    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    logger.info("SQLite tables auto-created via Base.metadata.create_all().")


def initialize_db(
    *,
    database_url: Optional[str] = None,
    pool_size: int = 20,
    max_overflow: int = 10,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global _engine
    url = database_url or settings.DATABASE_URL
    try:
        if _engine is not None:
            return _engine, async_session_factory
        _engine = _build_engine_from_url(url, pool_size=pool_size, max_overflow=max_overflow)
        async_session_factory.configure(bind=_engine)
        logger.info(
            "Database engine initialized.",
            extra={"pool_size": pool_size, "max_overflow": max_overflow},
        )

        # Auto-create tables for SQLite (development convenience)
        if _is_sqlite(url):
            _auto_create_sqlite_tables(_engine)

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
            async_session_factory.configure(bind=None)
            _engine = None


def get_sync_database_url() -> str:
    return settings.DATABASE_URL_SYNC or settings.DATABASE_URL
