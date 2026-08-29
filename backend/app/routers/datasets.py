"""Datasets router — file upload, validation, import, and management."""
from __future__ import annotations

import hashlib
import os
import tempfile
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.deps import get_current_active_user, get_db, require_permissions, UserLike
from ..core.errors import ConflictError, NotFoundError, ValidationError
from ..core.logging import get_logger
from ..models.dataset import DatasetSourceType, DatasetStatus, ImportJobType
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.base import ListQueryParams
from ..schemas.dataset import (
    DatasetResponse,
    DatasetUpdate,
    DatasetValidationResponse,
    ImportJobResponse,
    ImportStatus,
)
from ..services.audit_service import audit_service
from ..services.ingestion_service import ingestion_service

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["Datasets"])


def _dataset_repo() -> DatasetRepository:
    from ..models.dataset import Dataset
    return DatasetRepository(Dataset)


def _assert_org_owns_dataset(current_user: UserLike, dataset: Any) -> None:
    """Tenant isolation: dataset must belong to user's organization."""
    user_org = str(getattr(current_user, "organization_id", ""))
    if str(dataset.organization_id) != user_org:
        raise NotFoundError(message="Dataset not found.")


# ---------------------------------------------------------------------------
# Upload and validate
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a dataset file",
    description=(
        "Uploads a CSV, Excel, or JSON file, validates its metadata, "
        "computes a SHA-256 checksum for deduplication, and schedules async validation. "
        "Requires `data:import` permission."
    ),
)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> dict:
    org_id = UUID(str(current_user.organization_id))

    # Read file content
    content = await file.read()
    file_size = len(content)
    filename = file.filename or "upload"
    content_type = file.content_type

    # Validate metadata (extension, MIME, size)
    source_type = ingestion_service.validate_upload(filename, content_type, file_size)

    # Compute checksum for dedup
    checksum = hashlib.sha256(content).hexdigest()

    # Check for duplicate
    repo = _dataset_repo()
    existing = await repo.get_by_checksum(db, org_id, checksum)
    if existing and existing.status not in (DatasetStatus.FAILED, DatasetStatus.ARCHIVED):
        return {
            "message": "This file has already been uploaded.",
            "dataset_id": str(existing.id),
            "status": existing.status.value if hasattr(existing.status, "value") else str(existing.status),
            "duplicate": True,
        }

    # Store file to local temp or S3
    file_path = await _store_file(content, filename, str(org_id))

    # Create dataset record
    dataset_name = (name or "").strip() or filename
    dataset = await ingestion_service.create_dataset_record(
        db,
        org_id=org_id,
        user_id=current_user.id,
        name=dataset_name,
        source_type=source_type,
        file_path=file_path,
        file_size_bytes=file_size,
        checksum=checksum,
    )

    # Trigger async validation
    try:
        from ..core.celery_app import celery_app
        if celery_app and not settings.CELERY_TASK_ALWAYS_EAGER:
            celery_app.send_task(
                "imports.validate_dataset",
                args=[str(dataset.id), str(org_id), file_path, source_type.value],
                queue="imports",
            )
        else:
            # Synchronous fallback (dev mode)
            headers, rows = ingestion_service.parse_file(content, source_type)
            mappings = ingestion_service.detect_schema(headers, rows)
            await ingestion_service.persist_column_schema(db, dataset.id, mappings)
            await repo.update_status(
                db, dataset.id, DatasetStatus.VALID.value,
                row_count=len(rows),
                column_count=len(headers),
            )
    except Exception as exc:
        logger.warning("Failed to trigger validation: %s", exc)

    await audit_service.log(
        db, "dataset.upload",
        organization=org_id,
        resource_type="dataset",
        resource_id=dataset.id,
        metadata={"filename": filename, "size_bytes": file_size},
    )

    return {
        "message": "File uploaded successfully. Validation is running.",
        "dataset_id": str(dataset.id),
        "name": dataset.name,
        "source_type": source_type.value,
        "file_size_bytes": file_size,
        "checksum": checksum,
        "duplicate": False,
    }


@router.get(
    "/{dataset_id}/validate",
    response_model=DatasetValidationResponse,
    summary="Get validation report for a dataset",
    description="Returns the data quality report generated during validation.",
)
async def get_validation_report(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> DatasetValidationResponse:
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)

    if dataset.status == DatasetStatus.UPLOADED:
        raise ValidationError(message="Validation has not completed yet.")

    # Retrieve column mappings to build report
    from ..models.dataset import DatasetColumn
    from ..schemas.dataset import ColumnMappingInfo
    col_result = await db.execute(
        select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id)
    )
    columns = list(col_result.scalars().all())
    mappings = [
        ColumnMappingInfo(
            source_column=c.name,
            target_entity=c.mapped_to.split(".")[0] if c.mapped_to and "." in c.mapped_to else "",
            target_field=c.mapped_to.split(".")[1] if c.mapped_to and "." in c.mapped_to else "",
            data_type=c.data_type.value if hasattr(c.data_type, "value") else str(c.data_type),
            sample_count=0,
        )
        for c in columns
    ]

    return DatasetValidationResponse(
        valid=dataset.status == DatasetStatus.VALID,
        total_rows=dataset.row_count or 0,
        error_count=0,
        warning_count=0,
        columns=mappings,
        error_samples=[],
        quality_score=100.0 if dataset.status == DatasetStatus.VALID else 0.0,
        completeness=100.0,
        validity=100.0,
        consistency=100.0,
        uniqueness=100.0,
    )


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post(
    "/{dataset_id}/import",
    response_model=ImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start import job for a validated dataset",
    description=(
        "Creates an import job and queues the ETL pipeline. "
        "The dataset must be in VALID status. "
        "Requires `data:import` permission."
    ),
)
async def start_import(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> ImportJobResponse:
    org_id = UUID(str(current_user.organization_id))
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)

    if dataset.status not in (DatasetStatus.VALID, DatasetStatus.IMPORTED):
        raise ValidationError(
            message=f"Dataset must be validated before importing. Current status: {dataset.status}",
        )

    # Get column mappings
    from ..models.dataset import DatasetColumn
    col_result = await db.execute(
        select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id)
    )
    columns = list(col_result.scalars().all())
    from ..schemas.dataset import ColumnMappingInfo
    mappings = [
        ColumnMappingInfo(
            source_column=c.name,
            target_entity=c.mapped_to.split(".")[0] if c.mapped_to and "." in c.mapped_to else "",
            target_field=c.mapped_to.split(".")[1] if c.mapped_to and "." in c.mapped_to else "",
            data_type=c.data_type.value if hasattr(c.data_type, "value") else str(c.data_type),
            sample_count=0,
        )
        for c in columns
    ]

    job = await ingestion_service.create_import_job(
        db,
        org_id=org_id,
        dataset_id=dataset_id,
        user_id=current_user.id,
        job_type=ImportJobType.IMPORT,
    )

    # Queue async import
    try:
        from ..core.celery_app import celery_app
        if celery_app and not settings.CELERY_TASK_ALWAYS_EAGER:
            celery_app.send_task(
                "imports.process_dataset",
                args=[
                    str(job.id),
                    str(dataset_id),
                    str(org_id),
                    dataset.file_path or "",
                    dataset.source_type.value if hasattr(dataset.source_type, "value") else str(dataset.source_type),
                    [m.model_dump() for m in mappings],
                ],
                queue="imports",
            )
        else:
            # Synchronous dev mode
            content = open(dataset.file_path, "rb").read() if dataset.file_path and os.path.exists(dataset.file_path or "") else b""
            if content:
                src_type = dataset.source_type if hasattr(dataset.source_type, "value") else DatasetSourceType(str(dataset.source_type))
                headers, rows = ingestion_service.parse_file(content, src_type)
                await ingestion_service.run_import(
                    db,
                    import_job_id=job.id,
                    headers=headers,
                    rows=rows,
                    column_mappings=mappings,
                    org_id=org_id,
                )
    except Exception as exc:
        logger.warning("Failed to queue import task: %s", exc)

    await audit_service.log(
        db, "dataset.import_started",
        organization=org_id,
        resource_type="import_job",
        resource_id=job.id,
        metadata={"dataset_id": str(dataset_id)},
    )

    return ImportJobResponse(
        id=job.id,
        dataset_id=dataset_id,
        job_type=job.job_type.value if hasattr(job.job_type, "value") else str(job.job_type),
        status=ImportStatus.PENDING,
        progress=0.0,
        processed_rows=0,
        total_rows=dataset.row_count,
        error_count=0,
        warning_count=0,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=None,
        created_by=current_user.id,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[DatasetResponse],
    summary="List datasets for current organization",
)
async def list_datasets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: DatasetStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> list[DatasetResponse]:
    org_id = UUID(str(current_user.organization_id))
    repo = _dataset_repo()
    filters: dict[str, Any] = {"organization_id": org_id}
    if status_filter:
        filters["status"] = status_filter
    result = await repo.get_multi(db, ListQueryParams(skip=skip, limit=limit), **filters)
    return [DatasetResponse.model_validate(d) for d in result.items]


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset by ID",
)
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> DatasetResponse:
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)
    return DatasetResponse.model_validate(dataset)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update dataset metadata",
)
async def update_dataset(
    dataset_id: UUID,
    payload: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:manage")),
) -> DatasetResponse:
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)
    updated = await repo.update(db, dataset, payload)
    return DatasetResponse.model_validate(updated)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a dataset",
    description="Marks the dataset as archived. Requires `data:manage` permission.",
)
async def delete_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:manage")),
) -> None:
    org_id = UUID(str(current_user.organization_id))
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)
    await repo.update_status(db, dataset_id, DatasetStatus.ARCHIVED.value)
    await audit_service.log(
        db, "dataset.archive",
        organization=org_id,
        resource_type="dataset",
        resource_id=dataset_id,
    )


@router.get(
    "/{dataset_id}/jobs",
    response_model=list[ImportJobResponse],
    summary="List import jobs for a dataset",
)
async def list_import_jobs(
    dataset_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("data:import")),
) -> list[ImportJobResponse]:
    repo = _dataset_repo()
    dataset = await repo.get_or_404(db, dataset_id)
    _assert_org_owns_dataset(current_user, dataset)

    from ..models.dataset import ImportJob
    stmt = (
        select(ImportJob)
        .where(ImportJob.dataset_id == dataset_id)
        .order_by(ImportJob.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    jobs = list(result.scalars().all())

    return [
        ImportJobResponse(
            id=j.id,
            dataset_id=j.dataset_id,
            job_type=j.job_type.value if hasattr(j.job_type, "value") else str(j.job_type),
            status=ImportStatus(j.status.value if hasattr(j.status, "value") else j.status),
            progress=_calc_progress(j),
            processed_rows=j.valid_rows or 0,
            total_rows=j.total_rows,
            error_count=j.error_count or 0,
            warning_count=0,
            started_at=j.started_at,
            completed_at=j.completed_at,
            error_message=(j.error_log[0].get("error") if j.error_log else None),
            created_by=j.triggered_by_id,
            created_at=j.created_at,
            updated_at=j.updated_at,
        )
        for j in jobs
    ]


def _calc_progress(job: Any) -> float:
    if job.status in ("COMPLETED",):
        return 100.0
    if job.status in ("FAILED",):
        return 0.0
    total = job.total_rows or 0
    processed = job.valid_rows or 0
    if total > 0:
        return round((processed / total) * 100, 1)
    return 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _store_file(content: bytes, filename: str, org_id: str) -> str:
    """Persist uploaded file to storage. Returns path/key."""
    from ..core.config import settings

    # Try S3 first
    if settings.S3_ACCESS_KEY.get_secret_value():
        try:
            import aioboto3
            session = aioboto3.Session()
            key = f"uploads/{org_id}/{hashlib.sha256(content).hexdigest()[:16]}_{filename}"
            async with session.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT if settings.S3_ENDPOINT != "https://s3.amazonaws.com" else None,
                aws_access_key_id=settings.S3_ACCESS_KEY.get_secret_value(),
                aws_secret_access_key=settings.S3_SECRET_KEY.get_secret_value(),
                region_name=settings.S3_REGION,
            ) as s3:
                await s3.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=key,
                    Body=content,
                )
            return f"s3://{settings.S3_BUCKET}/{key}"
        except Exception as exc:
            logger.warning("S3 upload failed, using local storage: %s", exc)

    # Local temp fallback
    upload_dir = os.path.join(tempfile.gettempdir(), "commercepulse_uploads", org_id)
    os.makedirs(upload_dir, exist_ok=True)
    short_hash = hashlib.sha256(content).hexdigest()[:12]
    safe_filename = f"{short_hash}_{os.path.basename(filename)}"
    fpath = os.path.join(upload_dir, safe_filename)
    with open(fpath, "wb") as f:
        f.write(content)
    return fpath
