from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, OrganizationScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from .organization import Organization


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"


class Category(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    parent_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[Category.organization_id]",
    )
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        foreign_keys="[Category.parent_id]",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        foreign_keys="[Product.category_id]",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
        Index("ix_categories_org_parent", "organization_id", "parent_id"),
    )


class Product(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "products"

    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(4000),
        nullable=True,
    )
    brand: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    category_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status_enum"),
        nullable=False,
        default=ProductStatus.DRAFT,
        server_default=ProductStatus.DRAFT.value,
        index=True,
    )
    cost_price: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    retail_price: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    current_stock: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    total_revenue: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
        default=0,
    )
    total_orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_units_sold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_returns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="products",
        foreign_keys="[Product.organization_id]",
    )
    category: Mapped[Optional[Category]] = relationship(
        "Category",
        back_populates="products",
        foreign_keys=[category_id],
    )
    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_product_org_external_id"),
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
        Index("ix_products_org_status", "organization_id", "status"),
        Index("ix_products_org_category", "organization_id", "category_id"),
    )


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    product_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Any] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    variant_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    option_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    cost_price: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    retail_price: Mapped[Optional[Any]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
    )
    stock: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )

    product: Mapped[Product] = relationship(
        "Product",
        back_populates="variants",
        foreign_keys=[product_id],
    )

    __table_args__ = (
        Index("ix_product_variants_org_product", "organization_id", "product_id"),
    )


class InventoryItem(Base, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "inventory_items"

    variant_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[Optional[Any]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    quantity_available: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    reorder_level: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    last_restocked_at: Mapped[Optional[Any]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        foreign_keys="[InventoryItem.organization_id]",
    )
    variant: Mapped[Optional[ProductVariant]] = relationship(
        "ProductVariant",
        foreign_keys=[variant_id],
    )
    product: Mapped[Optional[Product]] = relationship(
        "Product",
        foreign_keys=[product_id],
    )

    __table_args__ = (
        Index("ix_inventory_items_org_product", "organization_id", "product_id"),
        Index("ix_inventory_items_org_variant", "organization_id", "variant_id"),
    )
