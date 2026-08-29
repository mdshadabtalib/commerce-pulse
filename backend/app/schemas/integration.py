from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import TimestampModel, UUIDModel


class IntegrationType(str, Enum):
    SHOPIFY = "SHOPIFY"
    WOOCOMMERCE = "WOOCOMMERCE"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    QUICKBOOKS = "QUICKBOOKS"
    XERO = "XERO"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    GOOGLE_ANALYTICS = "GOOGLE_ANALYTICS"
    FACEBOOK_ADS = "FACEBOOK_ADS"
    GOOGLE_ADS = "GOOGLE_ADS"
    AMAZON_SELLER_CENTRAL = "AMAZON_SELLER_CENTRAL"
    ETSY = "ETSY"
    SQUARE = "SQUARE"
    CUSTOM_WEBHOOK = "CUSTOM_WEBHOOK"
    CSV_UPLOAD = "CSV_UPLOAD"
    API = "API"


class IntegrationStatus(str, Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    SYNCING = "SYNCING"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class SyncStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"


class SyncDirection(str, Enum):
    PULL = "PULL"
    PUSH = "PUSH"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class IntegrationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    integration_type: IntegrationType
    display_name: str = Field(min_length=1, max_length=255)
    config: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] | None = None
    webhook_url: str | None = None
    settings: dict[str, Any] | None = None
    sync_schedule: str | None = None

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        return v.strip()


class IntegrationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None
    credentials: dict[str, Any] | None = None
    webhook_url: str | None = None
    settings: dict[str, Any] | None = None
    sync_schedule: str | None = None
    status: IntegrationStatus | None = None

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class IntegrationResponse(UUIDModel, TimestampModel):
    organization_id: UUID
    integration_type: IntegrationType
    display_name: str
    status: IntegrationStatus
    icon_url: str | None = None
    webhook_url: str | None = None
    sync_schedule: str | None = None
    last_sync_at: datetime | None = None
    next_sync_at: datetime | None = None
    sync_direction: SyncDirection = SyncDirection.PULL
    auto_sync_enabled: bool = True
    settings: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    masked_credentials: dict[str, Any] | None = None
    connected_by: UUID | None = None
    connected_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class IntegrationSyncRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    full_sync: bool = False
    entity_types: list[str] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    config: dict[str, Any] | None = None


class IntegrationSyncResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    sync_id: UUID
    integration_id: UUID
    status: SyncStatus
    is_full_sync: bool = False
    progress: float = 0.0
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    entity_types: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IntegrationOAuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    auth_url: str
    state: str | None = None
    expires_at: datetime | None = None


class IntegrationTestResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    success: bool
    message: str | None = None
    latency_ms: int | None = None
    connection_details: dict[str, Any] | None = None
