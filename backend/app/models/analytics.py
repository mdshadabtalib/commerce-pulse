from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, CreatedByMixin, OrganizationScopedMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer
    from .dataset import Dataset
    from .organization import Organization
    from .user import User


class APIKeyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
    FAILED = "FAILED"


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    SMS = "SMS"
    PUSH = "PUSH"


class WidgetType(str, enum.Enum):
    KPI = "KPI"
    LINE_CHART = "LINE_CHART"
    BAR_CHART = "BAR_CHART"
    PIE_CHART = "PIE_CHART"
    TABLE = "TABLE"
    METRIC_CARD = "METRIC_CARD"
    GAUGE = "GAUGE"
    HEATMAP = "HEATMAP"
    FUNNEL = "FUNNEL"
    CUSTOM = "CUSTOM"


class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TRIALING = "TRIALING"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    INACTIVE = "INACTIVE"


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    PENDING = "PENDING"


class IntegrationProvider(str, enum.Enum):
    SHOPIFY = "SHOPIFY"
    WOOCOMMERCE = "WOOCOMMERCE"
    STRIPE = "STRIPE"
    QUICKBOOKS = "QUICKBOOKS"
    XERO = "XERO"
    AMAZON = "AMAZON"
    ETSY = "ETSY"
    SQUARE = "SQUARE"
    CUSTOM = "CUSTOM"


class APIKey(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    scopes: Mapped[Optional[list[str]]] = mapped_column(
        JSON,
        nullable=True,
    )
    status: Mapped[APIKeyStatus] = mapped_column(
        Enum(APIKeyStatus, name="api_key_status_enum"),
        nullable=False,
        default=APIKeyStatus.ACTIVE,
        server_default=APIKeyStatus.ACTIVE.value,
        index=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    created_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    revoked_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[APIKey.organization_id]",
    )
    created_by_user: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="api_keys",
        foreign_keys=[created_by_id],
    )
    revoked_by_user: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[revoked_by_id],
    )

    __table_args__ = (
        Index("ix_api_keys_org_status", "organization_id", "status"),
        Index("ix_api_keys_org_created_at", "organization_id", "created_at"),
    )


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    organization_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    api_key_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    old_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    new_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="audit_logs",
        foreign_keys="[AuditLog.organization_id]",
    )
    user: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index("ix_audit_logs_org_action_resource", "organization_id", "action", "resource_type"),
        Index("ix_audit_logs_org_user_created", "organization_id", "user_id", "created_at"),
        Index("ix_audit_logs_org_created_at", "organization_id", "created_at"),
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel_enum"),
        nullable=False,
        default=NotificationChannel.IN_APP,
        server_default=NotificationChannel.IN_APP.value,
        index=True,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status_enum"),
        nullable=False,
        default=NotificationStatus.PENDING,
        server_default=NotificationStatus.PENDING.value,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    action_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    action_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    user: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="notifications",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_org_status", "organization_id", "status"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )


class Dashboard(Base, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dashboards"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    layout_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    filters: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    updated_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="dashboards",
        foreign_keys="[Dashboard.organization_id]",
    )
    created_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    updated_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[updated_by_id],
    )
    widgets: Mapped[list[DashboardWidget]] = relationship(
        "DashboardWidget",
        back_populates="dashboard",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_dashboard_org_slug"),
        Index("ix_dashboards_org_default", "organization_id", "is_default"),
        Index("ix_dashboards_org_created_at", "organization_id", "created_at"),
    )


class DashboardWidget(Base, TimestampMixin):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType, name="widget_type_enum"),
        nullable=False,
        default=WidgetType.KPI,
        server_default=WidgetType.KPI.value,
        index=True,
    )
    position: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    size: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    query_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    dataset_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    refresh_interval_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    dashboard: Mapped[Dashboard] = relationship(
        "Dashboard",
        back_populates="widgets",
        foreign_keys=[dashboard_id],
    )
    dataset: Mapped[Optional[Dataset]] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
    )

    __table_args__ = (
        Index("ix_dashboard_widgets_dashboard", "dashboard_id"),
        Index("ix_dashboard_widgets_org_widget_type", "organization_id", "widget_type"),
    )


class SavedReport(Base, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "saved_reports"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    filters: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    schedule: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    created_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_generated_report_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="reports",
        foreign_keys="[SavedReport.organization_id]",
    )
    created_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    last_generated_report: Mapped[Optional["Report"]] = relationship(
        "Report",
        foreign_keys=[last_generated_report_id],
    )
    generated_reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="saved_report",
        foreign_keys="[Report.saved_report_id]",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_saved_reports_org_type", "organization_id", "report_type"),
        Index("ix_saved_reports_org_created_at", "organization_id", "created_at"),
        Index("ix_saved_reports_org_favorite", "organization_id", "is_favorite"),
    )


class Report(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "reports"

    saved_report_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("saved_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PDF",
        server_default="PDF",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )
    date_range: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    filters: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    sections: Mapped[Optional[list[str]]] = mapped_column(
        JSON,
        nullable=True,
    )
    file_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    row_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    generated_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[Report.organization_id]",
    )
    saved_report: Mapped[Optional[SavedReport]] = relationship(
        "SavedReport",
        back_populates="generated_reports",
        foreign_keys=[saved_report_id],
    )
    generated_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[generated_by_id],
    )

    __table_args__ = (
        Index("ix_reports_org_status", "organization_id", "status"),
        Index("ix_reports_org_type_created", "organization_id", "report_type", "created_at"),
        Index("ix_reports_org_saved_report", "organization_id", "saved_report_id"),
    )


class Forecast(Base, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "forecasts"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="AUTO",
        server_default="AUTO",
    )
    horizon_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
    )
    confidence_level: Mapped[Any] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
        default=0.95,
        server_default="0.95",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )
    training_date_range: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    dataset_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_run_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("forecast_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="forecasts",
        foreign_keys="[Forecast.organization_id]",
    )
    dataset: Mapped[Optional[Dataset]] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
    )
    created_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    last_run: Mapped[Optional["ForecastRun"]] = relationship(
        "ForecastRun",
        foreign_keys=[last_run_id],
    )
    runs: Mapped[list["ForecastRun"]] = relationship(
        "ForecastRun",
        back_populates="forecast",
        foreign_keys="[ForecastRun.forecast_id]",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_forecasts_org_metric", "organization_id", "metric"),
        Index("ix_forecasts_org_status_created", "organization_id", "status", "created_at"),
    )


class ForecastRun(Base, TimestampMixin):
    __tablename__ = "forecast_runs"

    forecast_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_used: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
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
    training_points: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    forecast_points: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    actual_points: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    accuracy: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    training_duration_seconds: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    forecast: Mapped[Forecast] = relationship(
        "Forecast",
        back_populates="runs",
        foreign_keys=[forecast_id],
    )

    __table_args__ = (
        Index("ix_forecast_runs_forecast_status", "forecast_id", "status"),
        Index("ix_forecast_runs_org_created", "organization_id", "created_at"),
    )


class Anomaly(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "anomalies"

    dataset_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    anomaly_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="MEDIUM",
        server_default="MEDIUM",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DETECTED",
        server_default="DETECTED",
        index=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    value: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
    )
    expected_value: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    deviation: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    deviation_percentage: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    evidence: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    acknowledged_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="anomalies",
        foreign_keys="[Anomaly.organization_id]",
    )
    dataset: Mapped[Optional[Dataset]] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
    )
    acknowledged_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[acknowledged_by_id],
    )
    resolved_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[resolved_by_id],
    )

    __table_args__ = (
        Index("ix_anomalies_org_severity_status", "organization_id", "severity", "status"),
        Index("ix_anomalies_org_metric_detected", "organization_id", "metric", "detected_at"),
        Index("ix_anomalies_org_created_at", "organization_id", "created_at"),
    )


class CustomerSegment(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "customer_segments"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    segment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OTHER",
        server_default="OTHER",
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    criteria: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    rfm_min: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    rfm_max: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    customer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_revenue: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    avg_order_value: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    avg_frequency: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True,
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[CustomerSegment.organization_id]",
    )
    customers: Mapped[list[Customer]] = relationship(
        "Customer",
        back_populates="segment",
        foreign_keys="[Customer.segment_id]",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_customer_segment_org_name"),
        Index("ix_customer_segments_org_type", "organization_id", "segment_type"),
        Index("ix_customer_segments_org_rfm", "organization_id", "rfm_min", "rfm_max"),
    )


class Integration(Base, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "integrations"

    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider, name="integration_provider_enum"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, name="integration_status_enum"),
        nullable=False,
        default=IntegrationStatus.PENDING,
        server_default=IntegrationStatus.PENDING.value,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    credentials_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    webhook_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    sync_interval_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    connected_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="integrations",
        foreign_keys="[Integration.organization_id]",
    )
    connected_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[connected_by_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "external_id", name="uq_integration_org_provider_external"),
        Index("ix_integrations_org_provider_status", "organization_id", "provider", "status"),
        Index("ix_integrations_org_next_sync", "organization_id", "next_sync_at"),
    )


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan_enum"),
        nullable=False,
        default=SubscriptionPlan.FREE,
        server_default=SubscriptionPlan.FREE.value,
        index=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status_enum"),
        nullable=False,
        default=SubscriptionStatus.TRIALING,
        server_default=SubscriptionStatus.TRIALING.value,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    unit_amount: Mapped[Any] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0,
        server_default="0",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    features: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="subscriptions",
        foreign_keys=[organization_id],
    )
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        "UsageRecord",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_subscriptions_org_status_plan", "organization_id", "status", "plan"),
        Index("ix_subscriptions_current_period_end", "current_period_end"),
    )


class UsageRecord(Base, TimestampMixin):
    __tablename__ = "usage_records"

    subscription_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    usage_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    stripe_usage_record_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    subscription: Mapped[Subscription] = relationship(
        "Subscription",
        back_populates="usage_records",
        foreign_keys=[subscription_id],
    )

    __table_args__ = (
        UniqueConstraint("subscription_id", "metric", "usage_date", name="uq_usage_sub_metric_date"),
        Index("ix_usage_records_org_metric_date", "organization_id", "metric", "usage_date"),
        Index("ix_usage_records_sub_period", "subscription_id", "period_start", "period_end"),
    )
