from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, OrganizationScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from .customer import Address, Customer
    from .organization import Organization
    from .product import Product, ProductVariant
    from .user import User


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    RETURNED = "RETURNED"


class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"


class OrderSource(str, enum.Enum):
    MANUAL = "MANUAL"
    CSV_IMPORT = "CSV_IMPORT"
    API = "API"
    INTEGRATION = "INTEGRATION"


class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    STRIPE = "STRIPE"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    OTHER = "OTHER"


class ReturnStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    SHIPPED = "SHIPPED"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Order(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "orders"

    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    order_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    customer_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        index=True,
    )
    subtotal: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    tax_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    shipping_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    discount_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    total_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.UNPAID,
        server_default=PaymentStatus.UNPAID.value,
        index=True,
    )
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"),
        nullable=True,
    )
    shipping_address_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    billing_address_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source: Mapped[OrderSource] = mapped_column(
        Enum(OrderSource, name="order_source_enum"),
        nullable=False,
        default=OrderSource.MANUAL,
        server_default=OrderSource.MANUAL.value,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="orders",
        foreign_keys="[Order.organization_id]",
    )
    customer: Mapped[Optional[Customer]] = relationship(
        "Customer",
        back_populates="orders",
        foreign_keys=[customer_id],
    )
    shipping_address: Mapped[Optional[Address]] = relationship(
        "Address",
        foreign_keys=[shipping_address_id],
    )
    billing_address: Mapped[Optional[Address]] = relationship(
        "Address",
        foreign_keys=[billing_address_id],
    )
    line_items: Mapped[list["OrderLineItem"]] = relationship(
        "OrderLineItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    refunds: Mapped[list["Refund"]] = relationship(
        "Refund",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    returns: Mapped[list["Return"]] = relationship(
        "Return",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_order_org_external_id"),
        UniqueConstraint("organization_id", "order_number", name="uq_order_org_order_number"),
        Index("ix_orders_organization_order_date", "organization_id", "order_date"),
        Index("ix_orders_organization_customer", "organization_id", "customer_id"),
        Index("ix_orders_org_status_order_date", "organization_id", "status", "order_date"),
    )


class OrderLineItem(Base, TimestampMixin):
    __tablename__ = "order_line_items"

    order_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variant_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name_snapshot: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    sku_snapshot: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    unit_price: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    discount_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    tax_amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    line_total: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
        default=0,
    )
    cost_unit_price: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    returned_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="line_items",
        foreign_keys=[order_id],
    )
    product: Mapped[Optional[Product]] = relationship(
        "Product",
        foreign_keys=[product_id],
    )
    variant: Mapped[Optional[ProductVariant]] = relationship(
        "ProductVariant",
        foreign_keys=[variant_id],
    )
    returns: Mapped[list["Return"]] = relationship(
        "Return",
        back_populates="line_item",
        foreign_keys="[Return.line_item_id]",
    )

    __table_args__ = (
        Index("ix_order_line_items_org_order", "organization_id", "order_id"),
        Index("ix_order_line_items_org_product", "organization_id", "product_id"),
    )


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    order_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
    )
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PAID,
        server_default=PaymentStatus.PAID.value,
        index=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_response: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="payments",
        foreign_keys=[order_id],
    )
    refunds: Mapped[list["Refund"]] = relationship(
        "Refund",
        back_populates="payment",
        foreign_keys="[Refund.payment_id]",
    )

    __table_args__ = (
        Index("ix_payments_org_order", "organization_id", "order_id"),
        Index("ix_payments_transaction_id", "transaction_id"),
    )


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    order_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Any] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    refunded_by_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="refunds",
        foreign_keys=[order_id],
    )
    payment: Mapped[Optional[Payment]] = relationship(
        "Payment",
        back_populates="refunds",
        foreign_keys=[payment_id],
    )
    refunded_by: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[refunded_by_id],
    )

    __table_args__ = (
        Index("ix_refunds_org_order", "organization_id", "order_id"),
        Index("ix_refunds_org_payment", "organization_id", "payment_id"),
    )


class Return(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "returns"

    order_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_item_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("order_line_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus, name="return_status_enum"),
        nullable=False,
        default=ReturnStatus.REQUESTED,
        server_default=ReturnStatus.REQUESTED.value,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[Return.organization_id]",
    )
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="returns",
        foreign_keys=[order_id],
    )
    customer: Mapped[Optional[Customer]] = relationship(
        "Customer",
        back_populates="returns",
        foreign_keys=[customer_id],
    )
    line_item: Mapped[Optional[OrderLineItem]] = relationship(
        "OrderLineItem",
        back_populates="returns",
        foreign_keys=[line_item_id],
    )

    __table_args__ = (
        Index("ix_returns_org_order", "organization_id", "order_id"),
        Index("ix_returns_org_customer", "organization_id", "customer_id"),
        Index("ix_returns_org_status", "organization_id", "status"),
    )
