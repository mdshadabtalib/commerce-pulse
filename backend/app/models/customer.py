from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, OrganizationScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from .analytics import CustomerSegment
    from .order import Order, Return
    from .organization import Organization


class AddressType(str, enum.Enum):
    SHIPPING = "SHIPPING"
    BILLING = "BILLING"
    BOTH = "BOTH"


class Customer(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "customers"

    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    marketing_opt_in: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    total_spent: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
        default=0,
    )
    order_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_order_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    first_order_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rfm_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    segment_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("customer_segments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="customers",
        foreign_keys="[Customer.organization_id]",
    )
    addresses: Mapped[list[Address]] = relationship(
        "Address",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="customer",
        foreign_keys="[Order.customer_id]",
    )
    returns: Mapped[list[Return]] = relationship(
        "Return",
        back_populates="customer",
        foreign_keys="[Return.customer_id]",
    )
    segment: Mapped[Optional[CustomerSegment]] = relationship(
        "CustomerSegment",
        back_populates="customers",
        foreign_keys=[segment_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_customer_org_external_id"),
        Index("ix_customers_organization_created_at", "organization_id", "created_at"),
        Index("ix_customers_organization_email", "organization_id", "email"),
        Index("ix_customers_segment", "segment_id"),
    )


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    customer_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[AddressType] = mapped_column(
        Enum(AddressType, name="address_type_enum"),
        nullable=False,
        default=AddressType.BOTH,
        server_default=AddressType.BOTH.value,
    )
    line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    country_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    customer: Mapped[Optional[Customer]] = relationship(
        "Customer",
        back_populates="addresses",
        foreign_keys=[customer_id],
    )

    __table_args__ = (
        Index("ix_addresses_organization_id", "organization_id"),
        Index("ix_addresses_customer_default", "customer_id", "is_default"),
    )
