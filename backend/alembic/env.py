"""Alembic environment configuration for CommercePulse.

This file:
- Loads the app settings to get DATABASE_URL
- Imports ALL SQLAlchemy models so Alembic can detect schema changes
- Supports both online (direct DB connection) and offline (SQL script) modes
- Uses the synchronous psycopg2 driver for Alembic (not asyncpg)
"""
from __future__ import annotations

import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# ---------------------------------------------------------------------------
# Ensure the backend package is importable when running alembic from the
# backend/ directory (alembic.ini sets prepend_sys_path = .)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Import Base so Alembic's autogenerate can see all mapped tables.
# Importing the models __init__ triggers all model registrations.
# ---------------------------------------------------------------------------
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402  — registers every model with Base.metadata

# ---------------------------------------------------------------------------
# Alembic Config object (wraps alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Override sqlalchemy.url with the app's synchronous DATABASE_URL so we
# never have to duplicate the connection string in alembic.ini.
# ---------------------------------------------------------------------------
try:
    from app.core.config import settings
    sync_url = settings.DATABASE_URL_SYNC
    if sync_url:
        config.set_main_option("sqlalchemy.url", sync_url)
except Exception as exc:
    # Fall back to whatever is in alembic.ini if settings can't be loaded
    import warnings
    warnings.warn(f"Could not load app settings for Alembic: {exc}", stacklevel=1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Metadata for autogenerate
# ---------------------------------------------------------------------------
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Render item filter — exclude PostGIS / extension tables from autogenerate
# ---------------------------------------------------------------------------
EXCLUDE_TABLES: set[str] = {"spatial_ref_sys"}


def include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN001
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


# ---------------------------------------------------------------------------
# Offline mode: produce a SQL script instead of connecting to the DB
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL (no live DB connection needed).
    Calls ``context.execute()`` which emits SQL to stdout / a file.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode: migrate against a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine, obtains a connection, and runs migrations within a
    transaction. Uses NullPool so each migration run opens exactly one
    connection and closes it cleanly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enable pg_trgm / uuid-ossp extensions if available (best-effort)
        try:
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
            connection.commit()
        except Exception:
            connection.rollback()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
