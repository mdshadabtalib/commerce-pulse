from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import Currency, TimestampModel, UUIDModel


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class ProductCategory(str, Enum):
    PHYSICAL = "PHYSICAL"
    DIGITAL = "DIGITAL"
    SERVICE = "SERVICE"
    SUBSCRIPTION = "SUBSCRIPTION"
    BUNDLE = "BUNDLE"
    OTHER = "OTHER"


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str = Field(min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=100)
    external_id: str | None = None
    category: ProductCategory = ProductCategory.PHYSICAL
    status: ProductStatus = ProductStatus.ACTIVE
    description: str | None = None
    short_description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    category_id: UUID | None = None
    currency: Currency = Currency.USD
    price: float = Field(default=0.0, ge=0)
    cost: float = Field(default=0.0, ge=0)
    compare_at_price: float | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, ge=0)
    weight_unit: str | None = None
    dimensions: dict[str, Any] | None = None
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_digital: bool = False
    requires_shipping: bool = True
    is_taxable: bool = True
    tax_rate: float | None = Field(default=None, ge=0, le=100)
    barcode: str | None = None
    hs_code: str | None = None
    country_of_origin: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name", "sku", "external_id", "brand", "manufacturer", "barcode", "hs_code", "country_of_origin")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class ProductUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=100)
    category: ProductCategory | None = None
    status: ProductStatus | None = None
    description: str | None = None
    short_description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    category_id: UUID | None = None
    currency: Currency | None = None
    price: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    compare_at_price: float | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, ge=0)
    weight_unit: str | None = None
    dimensions: dict[str, Any] | None = None
    images: list[str] | None = None
    tags: list[str] | None = None
    is_digital: bool | None = None
    requires_shipping: bool | None = None
    is_taxable: bool | None = None
    tax_rate: float | None = Field(default=None, ge=0, le=100)
    barcode: str | None = None
    hs_code: str | None = None
    country_of_origin: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name", "sku", "brand", "manufacturer", "barcode", "hs_code", "country_of_origin")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class ProductResponse(UUIDModel, TimestampModel):
    organization_id: UUID
    external_id: str | None = None
    name: str
    sku: str | None = None
    category: ProductCategory
    status: ProductStatus
    description: str | None = None
    short_description: str | None = None
    brand: str | None = None
    manufacturer: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    currency: Currency
    price: float
    cost: float
    compare_at_price: float | None = None
    profit_margin: float | None = None
    markup_percentage: float | None = None
    weight: float | None = None
    weight_unit: str | None = None
    dimensions: dict[str, Any] | None = None
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_digital: bool = False
    requires_shipping: bool = True
    is_taxable: bool = True
    tax_rate: float | None = None
    barcode: str | None = None
    hs_code: str | None = None
    country_of_origin: str | None = None
    inventory_quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0
    reorder_level: int | None = None
    reorder_quantity: int | None = None
    last_restocked_at: datetime | None = None
    total_orders: int = 0
    total_units_sold: int = 0
    total_revenue: float = 0.0
    total_profit: float = 0.0
    average_rating: float | None = None
    review_count: int = 0
    metadata: dict[str, Any] | None = None


class ProductPerformance(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    product_id: UUID
    name: str
    sku: str | None = None
    revenue: float = 0.0
    profit: float = 0.0
    profit_margin: float = 0.0
    units_sold: int = 0
    orders_count: int = 0
    return_rate: float = 0.0
    discount_dependency: float = 0.0
    avg_discount_percent: float | None = None
    contribution_margin: float | None = None
    inventory_turnover: float | None = None
    days_of_inventory_on_hand: float | None = None
    stockout_rate: float | None = None
    category: str | None = None
    brand: str | None = None
    currency: Currency = Currency.USD


class ProductMatrixPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    revenue_percentile: float = Field(ge=0.0, le=100.0)
    profit_margin_percentile: float = Field(ge=0.0, le=100.0)
    product_ids_in_quadrant: list[UUID] = Field(default_factory=list)
    quadrant_name: str | None = None
    description: str | None = None
