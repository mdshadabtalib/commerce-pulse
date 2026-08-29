from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import DateRangeFilter, TimestampModel, UUIDModel


class TrendDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class ForecastMetric(str, Enum):
    REVENUE = "REVENUE"
    ORDERS = "ORDERS"
    UNITS_SOLD = "UNITS_SOLD"


class ForecastModelType(str, Enum):
    AUTO = "AUTO"
    ARIMA = "ARIMA"
    SARIMA = "SARIMA"
    PROPHET = "PROPHET"
    XGBOOST = "XGBOOST"
    LSTM = "LSTM"
    ETS = "ETS"


class InsightType(str, Enum):
    OBSERVATION = "OBSERVATION"
    FACT = "FACT"
    STATISTICAL = "STATISTICAL"
    HYPOTHESIS = "HYPOTHESIS"
    RECOMMENDATION = "RECOMMENDATION"


class InsightSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InsightCategory(str, Enum):
    SALES = "SALES"
    CUSTOMER = "CUSTOMER"
    PRODUCT = "PRODUCT"
    INVENTORY = "INVENTORY"
    MARKETING = "MARKETING"
    FINANCIAL = "FINANCIAL"
    OPERATIONAL = "OPERATIONAL"


class ReportType(str, Enum):
    SALES_SUMMARY = "SALES_SUMMARY"
    CUSTOMER_INSIGHTS = "CUSTOMER_INSIGHTS"
    PRODUCT_PERFORMANCE = "PRODUCT_PERFORMANCE"
    FINANCIAL_SUMMARY = "FINANCIAL_SUMMARY"
    FORECAST_REPORT = "FORECAST_REPORT"
    CUSTOM = "CUSTOM"


class ReportFormat(str, Enum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    HTML = "HTML"
    JSON = "JSON"


class AnomalyStatus(str, Enum):
    DETECTED = "DETECTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ForecastStatus(str, Enum):
    PENDING = "PENDING"
    TRAINING = "TRAINING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TimeSeriesPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    date: datetime | date
    value: float
    label: str | None = None


class KPIData(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    label: str
    value: float
    previous_value: float | None = None
    growth_rate: float | None = None
    unit: str | None = None
    trend: TrendDirection | None = None


class SalesKPIs(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    gross_revenue: float = 0.0
    net_revenue: float = 0.0
    profit: float = 0.0
    profit_margin: float = 0.0
    orders_count: int = 0
    units_sold: int = 0
    aov: float = 0.0
    asp: float = 0.0
    discount_amount: float = 0.0
    return_rate: float = 0.0
    refund_amount: float = 0.0


class PeriodComparison(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    current_period: SalesKPIs
    previous_period: SalesKPIs
    growth_rates: dict[str, float] = Field(default_factory=dict)


class BreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str
    value: float
    percentage: float | None = None


class ForecastPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    date: date | datetime
    forecast_value: float
    lower: float
    upper: float


class ForecastAccuracy(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    MAE: float | None = None
    RMSE: float | None = None
    MAPE: float | None = None
    SMAPE: float | None = None


class ForecastRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    metric: ForecastMetric
    horizon_days: int = Field(default=30, ge=1, le=365)
    model_type: ForecastModelType = ForecastModelType.AUTO
    date_range: DateRangeFilter | None = None
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    metric: ForecastMetric
    model_used: ForecastModelType
    horizon_days: int
    points: list[ForecastPoint]
    actual_points: list[TimeSeriesPoint]
    accuracy: ForecastAccuracy | None = None
    training_period: DateRangeFilter | None = None
    validation_period: DateRangeFilter | None = None
    status: ForecastStatus
    created_at: datetime
    completed_at: datetime | None = None


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    organization_id: UUID
    dataset_id: UUID | None = None
    metric: str
    anomaly_type: str
    severity: AnomalySeverity
    status: AnomalyStatus
    detected_at: datetime
    value: float
    expected_value: float | None = None
    deviation: float | None = None
    deviation_percentage: float | None = None
    description: str | None = None
    evidence: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    acknowledged_by: UUID | None = None
    acknowledged_at: datetime | None = None
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Insight(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    category: InsightCategory
    type: InsightType
    title: str
    description: str
    severity: InsightSeverity = InsightSeverity.LOW
    evidence: dict[str, Any] | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    date_range: DateRangeFilter
    filters: dict[str, Any] | None = None
    sections: list[str] | None = None
    include_charts: bool = True
    include_raw_data: bool = False


class ReportResponse(UUIDModel, TimestampModel):
    organization_id: UUID
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    title: str | None = None
    date_range: DateRangeFilter | None = None
    filters: dict[str, Any] | None = None
    sections: list[str] | None = None
    file_size: int | None = None
    page_count: int | None = None
    generated_by: UUID | None = None
    generated_at: datetime | None = None
    download_url: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None
