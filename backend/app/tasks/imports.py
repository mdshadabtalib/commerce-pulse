"""Import job Celery tasks — async ETL execution."""
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
    """Run an async coroutine from a sync Celery task."""
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
    name="imports.process_dataset",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="imports",
    acks_late=True,
    time_limit=1800,
    soft_time_limit=1700,
)
def process_dataset(
    self: Any,
    import_job_id: str,
    dataset_id: str,
    org_id: str,
    file_path: str,
    source_type: str,
    column_mappings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute a dataset import job asynchronously.

    Reads the uploaded file, applies column mappings, runs ETL into domain
    tables (customers, products, orders), and updates import job status.

    Args:
        import_job_id: UUID of the ImportJob record.
        dataset_id: UUID of the Dataset record.
        org_id: UUID of the owning organization.
        file_path: S3 or local path of the uploaded file.
        source_type: DatasetSourceType value (CSV/EXCEL/JSON).
        column_mappings: Optional pre-supplied column mapping overrides.
    """
    async def _run() -> dict[str, Any]:
        from ..db.session import async_session_factory
        from ..services.ingestion_service import ingestion_service, IngestionService
        from ..schemas.dataset import ColumnMappingInfo
        from ..models.dataset import DatasetSourceType

        svc = IngestionService()

        async with async_session_factory() as db:
            try:
                # Read file from storage
                data = await _read_file(file_path)
                src_type = DatasetSourceType(source_type)
                headers, rows = svc.parse_file(data, src_type)

                # Build column mapping objects
                if column_mappings:
                    mappings = [ColumnMappingInfo(**m) for m in column_mappings]
                else:
                    mappings = svc.detect_schema(headers, rows)

                # Run ETL
                result = await svc.run_import(
                    db,
                    import_job_id=UUID(import_job_id),
                    headers=headers,
                    rows=rows,
                    column_mappings=mappings,
                    org_id=UUID(org_id),
                )
                await db.commit()
                logger.info(
                    "Dataset import completed.",
                    extra={"import_job_id": import_job_id, "result": result},
                )
                return result
            except Exception as exc:
                await db.rollback()
                # Mark job as failed
                try:
                    from sqlalchemy import select, update
                    from ..models.dataset import ImportJob, ImportJobStatus
                    from datetime import datetime, timezone
                    async with async_session_factory() as err_db:
                        stmt = select(ImportJob).where(ImportJob.id == UUID(import_job_id))
                        r = await err_db.execute(stmt)
                        job = r.scalar_one_or_none()
                        if job:
                            job.status = ImportJobStatus.FAILED
                            job.error_count = 1
                            job.error_log = [{"error": str(exc)[:500]}]
                            from datetime import datetime, timezone
                            job.completed_at = datetime.now(timezone.utc)
                            err_db.add(job)
                            await err_db.commit()
                except Exception:
                    pass
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(
            "Import task failed.",
            extra={"import_job_id": import_job_id, "error": str(exc)},
        )
        raise self.retry(exc=exc)


async def _read_file(file_path: str) -> bytes:
    """Read file bytes from local path or S3."""
    import os
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f.read()

    # Try S3
    try:
        import aioboto3
        from ..core.config import settings
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT if settings.S3_ENDPOINT != "https://s3.amazonaws.com" else None,
            aws_access_key_id=settings.S3_ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=settings.S3_SECRET_KEY.get_secret_value(),
            region_name=settings.S3_REGION,
        ) as s3:
            # file_path format: s3://bucket/key  or  bucket/key
            path = file_path.removeprefix("s3://")
            parts = path.split("/", 1)
            bucket, key = parts[0], parts[1] if len(parts) > 1 else path
            response = await s3.get_object(Bucket=bucket, Key=key)
            return await response["Body"].read()
    except Exception as exc:
        raise FileNotFoundError(f"Cannot read file from {file_path}: {exc}") from exc


@celery_app.task(  # type: ignore[attr-defined]
    name="imports.validate_dataset",
    bind=True,
    max_retries=1,
    queue="imports",
    acks_late=True,
    time_limit=300,
)
def validate_dataset(
    self: Any,
    dataset_id: str,
    org_id: str,
    file_path: str,
    source_type: str,
) -> dict[str, Any]:
    """Async dataset validation — runs schema detection and quality checks."""
    async def _run() -> dict[str, Any]:
        from ..db.session import async_session_factory
        from ..services.ingestion_service import IngestionService
        from ..models.dataset import DatasetSourceType, DatasetStatus
        from ..repositories.dataset_repository import DatasetRepository
        from ..models.dataset import Dataset

        svc = IngestionService()
        src_type = DatasetSourceType(source_type)

        async with async_session_factory() as db:
            repo = DatasetRepository(Dataset)
            await repo.update_status(db, UUID(dataset_id), DatasetStatus.VALIDATING.value)
            await db.commit()

            try:
                data = await _read_file(file_path)
                headers, rows = svc.parse_file(data, src_type)
                mappings = svc.detect_schema(headers, rows)
                report = svc.validate_data(headers, rows, mappings)

                async with async_session_factory() as db2:
                    new_status = DatasetStatus.VALID if report.valid else DatasetStatus.INVALID
                    await repo.update_status(db2, UUID(dataset_id), new_status.value,
                                             row_count=report.total_rows,
                                             column_count=len(headers))
                    await svc.persist_column_schema(db2, UUID(dataset_id), mappings)
                    await db2.commit()

                return {
                    "dataset_id": dataset_id,
                    "valid": report.valid,
                    "total_rows": report.total_rows,
                    "quality_score": report.quality_score,
                    "error_count": report.error_count,
                }
            except Exception as exc:
                async with async_session_factory() as db3:
                    await repo.update_status(db3, UUID(dataset_id), DatasetStatus.FAILED.value)
                    await db3.commit()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("Validation task failed.", extra={"dataset_id": dataset_id, "error": str(exc)})
        raise self.retry(exc=exc)
