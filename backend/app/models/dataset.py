from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, OrganizationScopedMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class DatasetSourceType(str, enum.Enum):
    CSV = "CSV"
    EXCEL = "EXCEL"
    JSON = "JSON"
    SHOPIFY = "SHOPIFY"
    WOOCOMMERCE = "WOOCOMMERCE"
    MANUAL = "MANUAL"


class DatasetStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    PROCESSING = "PROCESSING"
    IMPORTED = "IMPORTED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class ColumnDataType(str, enum.Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    CURRENCY = "CURRENCY"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    UNKNOWN = "UNKNOWN"


class ImportJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportJobType(str, enum.Enum):
    VALIDATION = "VALIDATION"
    IMPORT = "IMPORT"
    REIMPORT = "REIMPORT"


class Dataset(Base, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    source_type: Mapped[DatasetSourceType] = mapped_column(
        Enum(DatasetSourceType, name="dataset_source_type_enum"),
        nullable=False,
        default=DatasetSourceType.CSV,
        server_default=DatasetSourceType.CSV.value,
        index=True,
    )
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, name="dataset_status_enum"),
        nullable=False,
        default=DatasetStatus.UPLOADED,
        server_default=DatasetStatus.UPLOADED.value,
        index=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    row_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    column_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    imported_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    import_job_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_imported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="datasets",
        foreign_keys="[Dataset.organization_id]",
    )
    imported_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[imported_by_id],
    )
    columns: Mapped[list["DatasetColumn"]] = relationship(
        "DatasetColumn",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    import_jobs: Mapped[list["ImportJob"]] = relationship(
        "ImportJob",
        back_populates="dataset",
        foreign_keys="[ImportJob.dataset_id]",
    )
    latest_import_job: Mapped[Optional["ImportJob"]] = relationship(
        "ImportJob",
        foreign_keys=[import_job_id],
    )

    __table_args__ = (
        Index("ix_datasets_org_status", "organization_id", "status"),
        Index("ix_datasets_org_source_type", "organization_id", "source_type"),
        Index("ix_datasets_org_created_at", "organization_id", "created_at"),
        Index("ix_datasets_checksum_org", "checksum", "organization_id"),
    )


class DatasetColumn(Base, TimestampMixin):
    __tablename__ = "dataset_columns"

    dataset_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    data_type: Mapped[ColumnDataType] = mapped_column(
        Enum(ColumnDataType, name="column_data_type_enum"),
        nullable=False,
        default=ColumnDataType.UNKNOWN,
        server_default=ColumnDataType.UNKNOWN.value,
    )
    mapped_to: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_nullable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    sample_values: Mapped[Optional[list[Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    dataset: Mapped[Dataset] = relationship(
        "Dataset",
        back_populates="columns",
        foreign_keys=[dataset_id],
    )

    __table_args__ = (
        Index("ix_dataset_columns_dataset", "dataset_id"),
        Index("ix_dataset_columns_dataset_name", "dataset_id", "name", unique=True),
    )


class ImportJob(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "import_jobs"

    dataset_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ImportJobStatus] = mapped_column(
        Enum(ImportJobStatus, name="import_job_status_enum"),
        nullable=False,
        default=ImportJobStatus.PENDING,
        server_default=ImportJobStatus.PENDING.value,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    valid_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    invalid_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    error_log: Mapped[Optional[list[Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    triggered_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[ImportJobType] = mapped_column(
        Enum(ImportJobType, name="import_job_type_enum"),
        nullable=False,
        default=ImportJobType.IMPORT,
        server_default=ImportJobType.IMPORT.value,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[ImportJob.organization_id]",
    )
    dataset: Mapped[Optional[Dataset]] = relationship(
        "Dataset",
        back_populates="import_jobs",
        foreign_keys=[dataset_id],
    )
    triggered_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[triggered_by_id],
    )

    __table_args__ = (
        Index("ix_import_jobs_org_status", "organization_id", "status"),
        Index("ix_import_jobs_org_dataset", "organization_id", "dataset_id"),
        Index("ix_import_jobs_org_created_at", "organization_id", "created_at"),
    )
