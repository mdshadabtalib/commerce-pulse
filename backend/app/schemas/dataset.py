from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import TimestampModel, UUIDModel


class DatasetSourceType(str, Enum):
    CSV = "CSV"
    EXCEL = "EXCEL"
    JSON = "JSON"
    SHOPIFY = "SHOPIFY"
    WOOCOMMERCE = "WOOCOMMERCE"
    MANUAL = "MANUAL"


class DatasetStatus(str, Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    PROCESSING = "PROCESSING"
    IMPORTED = "IMPORTED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class ImportStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DatasetCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str = Field(min_length=1, max_length=255)
    source_type: DatasetSourceType

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: DatasetStatus | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class ColumnMappingInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    source_column: str
    target_entity: str
    target_field: str
    data_type: str
    sample_count: int


class DatasetValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    valid: bool
    total_rows: int
    error_count: int
    warning_count: int
    columns: list[ColumnMappingInfo]
    error_samples: list[dict[str, Any]]
    quality_score: float
    completeness: float
    validity: float
    consistency: float
    uniqueness: float


class DatasetResponse(UUIDModel, TimestampModel):
    organization_id: UUID
    name: str
    source_type: DatasetSourceType
    status: DatasetStatus
    file_path: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    checksum: str | None = None
    last_imported_at: datetime | None = None
    last_validated_at: datetime | None = None
    imported_by_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ImportJobCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    dataset_id: UUID
    job_type: str
    column_mappings: list[dict[str, Any]] | None = None
    settings: dict[str, Any] | None = None


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    dataset_id: UUID
    job_type: str
    status: ImportStatus
    progress: float = 0.0
    processed_rows: int = 0
    total_rows: int | None = None
    error_count: int = 0
    warning_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
