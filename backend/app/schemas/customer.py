from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .common import TimestampModel, UUIDModel


class CustomerSegmentType(str, Enum):
    CHAMPIONS = "CHAMPIONS"
    LOYAL_CUSTOMERS = "LOYAL_CUSTOMERS"
    POTENTIAL_LOYALISTS = "POTENTIAL_LOYALISTS"
    NEW_CUSTOMERS = "NEW_CUSTOMERS"
    PROMISING = "PROMISING"
    NEED_ATTENTION = "NEED_ATTENTION"
    AT_RISK = "AT_RISK"
    CANNOT_LOSE_THEM = "CANNOT_LOSE_THEM"
    HIBERNATING = "HIBERNATING"
    LOST = "LOST"
    OTHER = "OTHER"


class CustomerCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    external_id: str

    @field_validator("first_name", "last_name", "external_id")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr | None) -> EmailStr | None:
        if v:
            return EmailStr(v.lower().strip())
        return v


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr | None) -> EmailStr | None:
        if v:
            return EmailStr(v.lower().strip())
        return v


class CustomerResponse(UUIDModel, TimestampModel):
    organization_id: UUID
    external_id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    total_orders: int = 0
    total_spent: float = 0.0
    total_items: int = 0
    avg_order_value: float = 0.0
    first_order_at: datetime | None = None
    last_order_at: datetime | None = None
    segment: CustomerSegmentType | None = None
    rfm_score: int | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class RFMRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    recency_days: int | None = Field(default=None, ge=1, le=730)
    use_default_thresholds: bool = True
    custom_ranges: dict[str, Any] | None = None


class RFMScores(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    customer_id: UUID
    recency_score: int = Field(ge=1, le=5)
    frequency_score: int = Field(ge=1, le=5)
    monetary_score: int = Field(ge=1, le=5)
    rfm_score: int = Field(ge=3, le=15)
    recency_days: int | None = None
    frequency_count: int | None = None
    monetary_value: float | None = None
    segment: CustomerSegmentType | None = None


class CustomerSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID | None = None
    name: str
    segment_type: CustomerSegmentType
    customer_count: int = 0
    total_revenue: float = 0.0
    avg_order_value: float = 0.0
    avg_frequency: float = 0.0
    recommended_action: str | None = None
    criteria: dict[str, Any] | None = None


class CohortData(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    cohort_month: date
    months_since_first_purchase: int
    customer_count: int | None = None
    revenue: float | None = None
