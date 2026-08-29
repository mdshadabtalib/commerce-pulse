from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, CreatedByMixin, OrganizationScopedMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .analytics import (
        APIKey,
        Anomaly,
        AuditLog,
        CustomerSegment,
        Dashboard,
        Forecast,
        Integration,
        Notification,
        Report,
        SavedReport,
        Subscription,
        UsageRecord,
    )
    from .customer import Address, Customer
    from .dataset import Dataset, ImportJob
    from .order import Order
    from .product import Category, Product, ProductVariant
    from .user import User


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    PAST_DUE = "PAST_DUE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class OrganizationSize(str, enum.Enum):
    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_500 = "201-500"
    SIZE_500_PLUS = "500+"


class DefaultCurrency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    SGD = "SGD"


class OrganizationMemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    REMOVED = "REMOVED"


class RoleTier(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class PermissionCategory(str, enum.Enum):
    ADMIN = "admin"
    ANALYTICS = "analytics"
    DATA = "data"
    BILLING = "billing"
    SETTINGS = "settings"
    REPORTS = "reports"


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )
    default_currency: Mapped[DefaultCurrency] = mapped_column(
        Enum(DefaultCurrency, name="default_currency_enum"),
        nullable=False,
        default=DefaultCurrency.USD,
        server_default=DefaultCurrency.USD.value,
    )
    locale: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en_US",
        server_default="en_US",
    )
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, name="organization_status_enum"),
        nullable=False,
        default=OrganizationStatus.TRIAL,
        server_default=OrganizationStatus.TRIAL.value,
        index=True,
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    billing_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    billing_address: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    size: Mapped[Optional[OrganizationSize]] = mapped_column(
        Enum(OrganizationSize, name="organization_size_enum"),
        nullable=True,
    )
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="created_organizations",
        foreign_keys=[created_by_id],
    )
    members: Mapped[list[OrganizationMember]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    roles: Mapped[list[Role]] = relationship(
        "Role",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    datasets: Mapped[list[Dataset]] = relationship(
        "Dataset",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    dashboards: Mapped[list[Dashboard]] = relationship(
        "Dashboard",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list[SavedReport]] = relationship(
        "SavedReport",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    customers: Mapped[list[Customer]] = relationship(
        "Customer",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    integrations: Mapped[list[Integration]] = relationship(
        "Integration",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    forecasts: Mapped[list[Forecast]] = relationship(
        "Forecast",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    anomalies: Mapped[list[Anomaly]] = relationship(
        "Anomaly",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_organizations_status_created_at", "status", "created_at"),
        Index("ix_organizations_slug", "slug", unique=True),
    )


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invited_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invite_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_owner: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    status: Mapped[OrganizationMemberStatus] = mapped_column(
        Enum(OrganizationMemberStatus, name="org_member_status_enum"),
        nullable=False,
        default=OrganizationMemberStatus.INVITED,
        server_default=OrganizationMemberStatus.INVITED.value,
        index=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="members",
        foreign_keys=[organization_id],
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="organization_memberships",
        foreign_keys=[user_id],
    )
    role: Mapped[Optional[Role]] = relationship(
        "Role",
        back_populates="members",
        foreign_keys=[role_id],
    )
    invited_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member_org_user"),
        Index("ix_org_members_org_status", "organization_id", "status"),
        Index("ix_org_members_user_status", "user_id", "status"),
    )


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    organization_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    tier: Mapped[RoleTier] = mapped_column(
        Enum(RoleTier, name="role_tier_enum"),
        nullable=False,
        default=RoleTier.VIEWER,
        server_default=RoleTier.VIEWER.value,
    )

    organization: Mapped[Optional[Organization]] = relationship(
        "Organization",
        back_populates="roles",
        foreign_keys=[organization_id],
    )
    members: Mapped[list[OrganizationMember]] = relationship(
        "OrganizationMember",
        back_populates="role",
        foreign_keys="[OrganizationMember.role_id]",
    )
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_roles_org_slug"),
        Index("ix_roles_org_tier", "organization_id", "tier"),
    )


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    category: Mapped[PermissionCategory] = mapped_column(
        Enum(PermissionCategory, name="permission_category_enum"),
        nullable=False,
        default=PermissionCategory.ANALYTICS,
        server_default=PermissionCategory.ANALYTICS.value,
        index=True,
    )

    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_permissions_category", "category"),
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[Role] = relationship(
        "Role",
        back_populates="role_permissions",
        foreign_keys=[role_id],
    )
    permission: Mapped[Permission] = relationship(
        "Permission",
        back_populates="role_permissions",
        foreign_keys=[permission_id],
    )

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
