from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .analytics import APIKey, AuditLog, Notification
    from .organization import Organization, OrganizationMember


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        server_default=UserStatus.PENDING_VERIFICATION.value,
        index=True,
    )
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    organization_memberships: Mapped[list[OrganizationMember]] = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_organizations: Mapped[list[Organization]] = relationship(
        "Organization",
        back_populates="created_by",
        foreign_keys="[Organization.created_by_id]",
    )
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey",
        back_populates="created_by_user",
        foreign_keys="[APIKey.created_by_id]",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="[AuditLog.user_id]",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="user",
        foreign_keys="[Notification.user_id]",
    )

    __table_args__ = (
        Index("ix_users_status_created_at", "status", "created_at"),
        Index("ix_users_email_lower", "email", postgresql_using="btree"),
    )
