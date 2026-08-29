from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    SGD = "SGD"


class UUIDModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID


class TimestampModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class ListQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = None
    sort_desc: bool = True
    search: str | None = None


class DateRangeFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    start_date: date | None = None
    end_date: date | None = None


class SuccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    success: bool = True
    message: str | None = None


class ErrorResponseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    error: ErrorResponseDetail
