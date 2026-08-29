"""Initial schema — all tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-29 00:00:00.000000

Creates all CommercePulse tables:
  users, organizations, organization_members, roles, permissions,
  role_permissions, customers, addresses, categories, products,
  product_variants, inventory_items, orders, order_line_items,
  payments, refunds, returns, datasets, dataset_columns, import_jobs,
  api_keys, audit_logs, notifications, dashboards, dashboard_widgets,
  saved_reports, reports, forecasts, forecast_runs, anomalies,
  customer_segments, integrations, subscriptions, usage_records
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # PostgreSQL extensions
    # ------------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # ------------------------------------------------------------------
    # Enum types
    # ------------------------------------------------------------------
    user_status_enum = sa.Enum(
        "ACTIVE", "INVITED", "SUSPENDED", "PENDING_VERIFICATION",
        name="user_status_enum",
    )
    org_status_enum = sa.Enum(
        "ACTIVE", "TRIAL", "PAST_DUE", "SUSPENDED", "CANCELLED",
        name="organization_status_enum",
    )
    org_size_enum = sa.Enum(
        "1-10", "11-50", "51-200", "201-500", "500+",
        name="organization_size_enum",
    )
    default_currency_enum = sa.Enum(
        "USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "SGD",
        name="default_currency_enum",
    )
    org_member_status_enum = sa.Enum(
        "ACTIVE", "INVITED", "REMOVED",
        name="org_member_status_enum",
    )
    role_tier_enum = sa.Enum(
        "owner", "admin", "analyst", "viewer",
        name="role_tier_enum",
    )
    permission_category_enum = sa.Enum(
        "admin", "analytics", "data", "billing", "settings", "reports",
        name="permission_category_enum",
    )
    address_type_enum = sa.Enum(
        "SHIPPING", "BILLING", "BOTH",
        name="address_type_enum",
    )
    product_status_enum = sa.Enum(
        "ACTIVE", "ARCHIVED", "DRAFT",
        name="product_status_enum",
    )
    order_status_enum = sa.Enum(
        "PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED", "RETURNED",
        name="order_status_enum",
    )
    payment_status_enum = sa.Enum(
        "UNPAID", "PAID", "PARTIALLY_REFUNDED", "REFUNDED",
        name="payment_status_enum",
    )
    payment_method_enum = sa.Enum(
        "CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "STRIPE",
        "BANK_TRANSFER", "CASH_ON_DELIVERY", "OTHER",
        name="payment_method_enum",
    )
    order_source_enum = sa.Enum(
        "MANUAL", "CSV_IMPORT", "API", "INTEGRATION",
        name="order_source_enum",
    )
    return_status_enum = sa.Enum(
        "REQUESTED", "APPROVED", "SHIPPED", "RECEIVED", "COMPLETED", "REJECTED",
        name="return_status_enum",
    )
    dataset_source_type_enum = sa.Enum(
        "CSV", "EXCEL", "JSON", "SHOPIFY", "WOOCOMMERCE", "MANUAL",
        name="dataset_source_type_enum",
    )
    dataset_status_enum = sa.Enum(
        "UPLOADED", "VALIDATING", "VALID", "INVALID", "PROCESSING", "IMPORTED", "FAILED", "ARCHIVED",
        name="dataset_status_enum",
    )
    column_data_type_enum = sa.Enum(
        "STRING", "INTEGER", "FLOAT", "DATE", "DATETIME", "BOOLEAN",
        "CURRENCY", "EMAIL", "PHONE", "UNKNOWN",
        name="column_data_type_enum",
    )
    import_job_status_enum = sa.Enum(
        "PENDING", "VALIDATING", "PROCESSING", "COMPLETED", "FAILED",
        name="import_job_status_enum",
    )
    import_job_type_enum = sa.Enum(
        "VALIDATION", "IMPORT", "REIMPORT",
        name="import_job_type_enum",
    )
    api_key_status_enum = sa.Enum(
        "ACTIVE", "REVOKED", "EXPIRED",
        name="api_key_status_enum",
    )
    notification_status_enum = sa.Enum(
        "PENDING", "SENT", "READ", "FAILED",
        name="notification_status_enum",
    )
    notification_channel_enum = sa.Enum(
        "EMAIL", "IN_APP", "SMS", "PUSH",
        name="notification_channel_enum",
    )
    widget_type_enum = sa.Enum(
        "KPI", "LINE_CHART", "BAR_CHART", "PIE_CHART", "TABLE",
        "METRIC_CARD", "GAUGE", "HEATMAP", "FUNNEL", "CUSTOM",
        name="widget_type_enum",
    )
    subscription_plan_enum = sa.Enum(
        "FREE", "BASIC", "PRO", "ENTERPRISE",
        name="subscription_plan_enum",
    )
    subscription_status_enum = sa.Enum(
        "ACTIVE", "TRIALING", "PAST_DUE", "CANCELED", "INACTIVE",
        name="subscription_status_enum",
    )
    integration_status_enum = sa.Enum(
        "CONNECTED", "DISCONNECTED", "ERROR", "PENDING",
        name="integration_status_enum",
    )
    integration_provider_enum = sa.Enum(
        "SHOPIFY", "WOOCOMMERCE", "STRIPE", "QUICKBOOKS", "XERO",
        "AMAZON", "ETSY", "SQUARE", "CUSTOM",
        name="integration_provider_enum",
    )

    # Create all enum types in DB
    for enum_type in [
        user_status_enum, org_status_enum, org_size_enum, default_currency_enum,
        org_member_status_enum, role_tier_enum, permission_category_enum,
        address_type_enum, product_status_enum, order_status_enum, payment_status_enum,
        payment_method_enum, order_source_enum, return_status_enum, dataset_source_type_enum,
        dataset_status_enum, column_data_type_enum, import_job_status_enum, import_job_type_enum,
        api_key_status_enum, notification_status_enum, notification_channel_enum, widget_type_enum,
        subscription_plan_enum, subscription_status_enum, integration_status_enum,
        integration_provider_enum,
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "INVITED", "SUSPENDED", "PENDING_VERIFICATION", name="user_status_enum"), nullable=False, server_default="PENDING_VERIFICATION"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_ip", sa.String(45), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_status_created_at", "users", ["status", "created_at"])
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_updated_at", "users", ["updated_at"])

    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.String(1024), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="UTC"),
        sa.Column("default_currency", sa.Enum("USD","EUR","GBP","INR","JPY","CAD","AUD","SGD", name="default_currency_enum"), nullable=False, server_default="USD"),
        sa.Column("locale", sa.String(10), nullable=False, server_default="en_US"),
        sa.Column("status", sa.Enum("ACTIVE","TRIAL","PAST_DUE","SUSPENDED","CANCELLED", name="organization_status_enum"), nullable=False, server_default="TRIAL"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("billing_address", sa.JSON(), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("size", sa.Enum("1-10","11-50","51-200","201-500","500+", name="organization_size_enum"), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_status_created_at", "organizations", ["status", "created_at"])
    op.create_index("ix_organizations_created_by_id", "organizations", ["created_by_id"])
    op.create_index("ix_organizations_created_at", "organizations", ["created_at"])
    op.create_index("ix_organizations_is_deleted", "organizations", ["is_deleted"])

    # ------------------------------------------------------------------
    # roles
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_index("ix_roles_created_at", "roles", ["created_at"])

    # ------------------------------------------------------------------
    # permissions
    # ------------------------------------------------------------------
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_permissions_slug", "permissions", ["slug"], unique=True)

    # ------------------------------------------------------------------
    # role_permissions
    # ------------------------------------------------------------------
    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # ------------------------------------------------------------------
    # organization_members
    # ------------------------------------------------------------------
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invited_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invite_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.Enum("ACTIVE","INVITED","REMOVED", name="org_member_status_enum"), nullable=False, server_default="INVITED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member_org_user"),
    )
    op.create_index("ix_org_members_org_status", "organization_members", ["organization_id", "status"])
    op.create_index("ix_org_members_user_status", "organization_members", ["user_id", "status"])
    op.create_index("ix_org_members_organization_id", "organization_members", ["organization_id"])
    op.create_index("ix_org_members_user_id", "organization_members", ["user_id"])

    # ------------------------------------------------------------------
    # customer_segments (must come before customers due to FK)
    # ------------------------------------------------------------------
    op.create_table(
        "customer_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("segment_type", sa.String(50), nullable=False, server_default="OTHER"),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("criteria", sa.JSON(), nullable=True),
        sa.Column("rfm_min", sa.Integer(), nullable=True),
        sa.Column("rfm_max", sa.Integer(), nullable=True),
        sa.Column("customer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("avg_order_value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("avg_frequency", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("recommended_action", sa.String(1024), nullable=True),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_customer_segment_org_name"),
    )
    op.create_index("ix_customer_segments_org_type", "customer_segments", ["organization_id", "segment_type"])
    op.create_index("ix_customer_segments_organization_id", "customer_segments", ["organization_id"])

    # ------------------------------------------------------------------
    # customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_spent", sa.Numeric(precision=18, scale=4), nullable=True, server_default="0"),
        sa.Column("order_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_order_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_order_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rfm_score", sa.Integer(), nullable=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["segment_id"], ["customer_segments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_customer_org_external_id"),
    )
    op.create_index("ix_customers_organization_created_at", "customers", ["organization_id", "created_at"])
    op.create_index("ix_customers_organization_email", "customers", ["organization_id", "email"])
    op.create_index("ix_customers_organization_id", "customers", ["organization_id"])
    op.create_index("ix_customers_segment", "customers", ["segment_id"])
    op.create_index("ix_customers_email", "customers", ["email"])

    # ------------------------------------------------------------------
    # addresses
    # ------------------------------------------------------------------
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Enum("SHIPPING","BILLING","BOTH", name="address_type_enum"), nullable=False, server_default="BOTH"),
        sa.Column("line1", sa.String(255), nullable=False),
        sa.Column("line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(50), nullable=True),
        sa.Column("country_code", sa.String(3), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_organization_id", "addresses", ["organization_id"])
    op.create_index("ix_addresses_customer_default", "addresses", ["customer_id", "is_default"])

    # ------------------------------------------------------------------
    # categories
    # ------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
    )
    op.create_index("ix_categories_org_parent", "categories", ["organization_id", "parent_id"])
    op.create_index("ix_categories_organization_id", "categories", ["organization_id"])

    # ------------------------------------------------------------------
    # products
    # ------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("sku", sa.String(255), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.String(4000), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE","ARCHIVED","DRAFT", name="product_status_enum"), nullable=False, server_default="DRAFT"),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("retail_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("current_stock", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("total_revenue", sa.Numeric(precision=18, scale=4), nullable=True, server_default="0"),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_units_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_returns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_product_org_external_id"),
        sa.UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
    )
    op.create_index("ix_products_org_status", "products", ["organization_id", "status"])
    op.create_index("ix_products_org_category", "products", ["organization_id", "category_id"])
    op.create_index("ix_products_organization_id", "products", ["organization_id"])

    # ------------------------------------------------------------------
    # product_variants
    # ------------------------------------------------------------------
    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(255), nullable=True),
        sa.Column("variant_name", sa.String(255), nullable=False),
        sa.Column("option_values", sa.JSON(), nullable=True),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("retail_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_variants_org_product", "product_variants", ["organization_id", "product_id"])

    # ------------------------------------------------------------------
    # inventory_items
    # ------------------------------------------------------------------
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=True),
        sa.Column("last_restocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_items_org_product", "inventory_items", ["organization_id", "product_id"])
    op.create_index("ix_inventory_items_org_variant", "inventory_items", ["organization_id", "variant_id"])
    op.create_index("ix_inventory_items_organization_id", "inventory_items", ["organization_id"])

    # ------------------------------------------------------------------
    # orders
    # ------------------------------------------------------------------
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("order_number", sa.String(100), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("PENDING","PAID","SHIPPED","DELIVERED","CANCELLED","REFUNDED","RETURNED", name="order_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("subtotal", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("shipping_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("payment_status", sa.Enum("UNPAID","PAID","PARTIALLY_REFUNDED","REFUNDED", name="payment_status_enum"), nullable=False, server_default="UNPAID"),
        sa.Column("payment_method", sa.Enum("CREDIT_CARD","DEBIT_CARD","PAYPAL","STRIPE","BANK_TRANSFER","CASH_ON_DELIVERY","OTHER", name="payment_method_enum"), nullable=True),
        sa.Column("shipping_address_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("billing_address_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.Enum("MANUAL","CSV_IMPORT","API","INTEGRATION", name="order_source_enum"), nullable=False, server_default="MANUAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["billing_address_id"], ["addresses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shipping_address_id"], ["addresses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_order_org_external_id"),
        sa.UniqueConstraint("organization_id", "order_number", name="uq_order_org_order_number"),
    )
    op.create_index("ix_orders_organization_order_date", "orders", ["organization_id", "order_date"])
    op.create_index("ix_orders_organization_customer", "orders", ["organization_id", "customer_id"])
    op.create_index("ix_orders_org_status_order_date", "orders", ["organization_id", "status", "order_date"])
    op.create_index("ix_orders_order_date", "orders", ["order_date"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_organization_id", "orders", ["organization_id"])

    # ------------------------------------------------------------------
    # order_line_items
    # ------------------------------------------------------------------
    op.create_table(
        "order_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name_snapshot", sa.String(512), nullable=False),
        sa.Column("sku_snapshot", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("cost_unit_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("returned_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_line_items_org_order", "order_line_items", ["organization_id", "order_id"])
    op.create_index("ix_order_line_items_org_product", "order_line_items", ["organization_id", "product_id"])
    op.create_index("ix_order_line_items_order_id", "order_line_items", ["order_id"])

    # ------------------------------------------------------------------
    # payments
    # ------------------------------------------------------------------
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", sa.String(255), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("method", sa.Enum("CREDIT_CARD","DEBIT_CARD","PAYPAL","STRIPE","BANK_TRANSFER","CASH_ON_DELIVERY","OTHER", name="payment_method_enum"), nullable=False),
        sa.Column("status", sa.Enum("UNPAID","PAID","PARTIALLY_REFUNDED","REFUNDED", name="payment_status_enum"), nullable=False, server_default="PAID"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_org_order", "payments", ["organization_id", "order_id"])
    op.create_index("ix_payments_transaction_id", "payments", ["transaction_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])

    # ------------------------------------------------------------------
    # refunds
    # ------------------------------------------------------------------
    op.create_table(
        "refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("reason", sa.String(1024), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["refunded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refunds_org_order", "refunds", ["organization_id", "order_id"])
    op.create_index("ix_refunds_org_payment", "refunds", ["organization_id", "payment_id"])

    # ------------------------------------------------------------------
    # returns
    # ------------------------------------------------------------------
    op.create_table(
        "returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reason", sa.String(1024), nullable=True),
        sa.Column("status", sa.Enum("REQUESTED","APPROVED","SHIPPED","RECEIVED","COMPLETED","REJECTED", name="return_status_enum"), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["line_item_id"], ["order_line_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_returns_org_order", "returns", ["organization_id", "order_id"])
    op.create_index("ix_returns_org_customer", "returns", ["organization_id", "customer_id"])
    op.create_index("ix_returns_org_status", "returns", ["organization_id", "status"])
    op.create_index("ix_returns_organization_id", "returns", ["organization_id"])

    # ------------------------------------------------------------------
    # datasets
    # ------------------------------------------------------------------
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.Enum("CSV","EXCEL","JSON","SHOPIFY","WOOCOMMERCE","MANUAL", name="dataset_source_type_enum"), nullable=False, server_default="CSV"),
        sa.Column("status", sa.Enum("UPLOADED","VALIDATING","VALID","INVALID","PROCESSING","IMPORTED","FAILED","ARCHIVED", name="dataset_status_enum"), nullable=False, server_default="UPLOADED"),
        sa.Column("file_path", sa.String(2048), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(255), nullable=True),
        sa.Column("imported_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["imported_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_datasets_org_status", "datasets", ["organization_id", "status"])
    op.create_index("ix_datasets_org_source_type", "datasets", ["organization_id", "source_type"])
    op.create_index("ix_datasets_org_created_at", "datasets", ["organization_id", "created_at"])
    op.create_index("ix_datasets_checksum_org", "datasets", ["checksum", "organization_id"])
    op.create_index("ix_datasets_checksum", "datasets", ["checksum"])
    op.create_index("ix_datasets_organization_id", "datasets", ["organization_id"])

    # ------------------------------------------------------------------
    # dataset_columns
    # ------------------------------------------------------------------
    op.create_table(
        "dataset_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("data_type", sa.Enum("STRING","INTEGER","FLOAT","DATE","DATETIME","BOOLEAN","CURRENCY","EMAIL","PHONE","UNKNOWN", name="column_data_type_enum"), nullable=False, server_default="UNKNOWN"),
        sa.Column("mapped_to", sa.String(255), nullable=True),
        sa.Column("is_nullable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sample_values", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "name", name="uq_dataset_column_name"),
    )
    op.create_index("ix_dataset_columns_dataset", "dataset_columns", ["dataset_id"])
    op.create_index("ix_dataset_columns_dataset_name", "dataset_columns", ["dataset_id", "name"], unique=True)

    # ------------------------------------------------------------------
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Enum("PENDING","VALIDATING","PROCESSING","COMPLETED","FAILED", name="import_job_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=True),
        sa.Column("valid_rows", sa.Integer(), nullable=True),
        sa.Column("invalid_rows", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.JSON(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("triggered_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", sa.Enum("VALIDATION","IMPORT","REIMPORT", name="import_job_type_enum"), nullable=False, server_default="IMPORT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_jobs_org_status", "import_jobs", ["organization_id", "status"])
    op.create_index("ix_import_jobs_org_dataset", "import_jobs", ["organization_id", "dataset_id"])
    op.create_index("ix_import_jobs_org_created_at", "import_jobs", ["organization_id", "created_at"])
    # Add deferred FK from datasets -> import_jobs
    op.create_foreign_key(
        "fk_datasets_import_job_id",
        "datasets", "import_jobs",
        ["import_job_id"], ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # api_keys
    # ------------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE","REVOKED","EXPIRED", name="api_key_status_enum"), nullable=False, server_default="ACTIVE"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_ip", sa.String(45), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revoked_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_org_status", "api_keys", ["organization_id", "status"])
    op.create_index("ix_api_keys_org_created_at", "api_keys", ["organization_id", "created_at"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_organization_id", "api_keys", ["organization_id"])

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(1024), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_org_action_resource", "audit_logs", ["organization_id", "action", "resource_type"])
    op.create_index("ix_audit_logs_org_user_created", "audit_logs", ["organization_id", "user_id", "created_at"])
    op.create_index("ix_audit_logs_org_created_at", "audit_logs", ["organization_id", "created_at"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])

    # ------------------------------------------------------------------
    # notifications
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("channel", sa.Enum("EMAIL","IN_APP","SMS","PUSH", name="notification_channel_enum"), nullable=False, server_default="IN_APP"),
        sa.Column("status", sa.Enum("PENDING","SENT","READ","FAILED", name="notification_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_url", sa.String(2048), nullable=True),
        sa.Column("action_text", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_status", "notifications", ["user_id", "status"])
    op.create_index("ix_notifications_org_status", "notifications", ["organization_id", "status"])
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])

    # ------------------------------------------------------------------
    # dashboards
    # ------------------------------------------------------------------
    op.create_table(
        "dashboards",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("layout_config", sa.JSON(), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_dashboard_org_slug"),
    )
    op.create_index("ix_dashboards_org_default", "dashboards", ["organization_id", "is_default"])
    op.create_index("ix_dashboards_org_created_at", "dashboards", ["organization_id", "created_at"])
    op.create_index("ix_dashboards_organization_id", "dashboards", ["organization_id"])

    # ------------------------------------------------------------------
    # dashboard_widgets
    # ------------------------------------------------------------------
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("dashboard_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("widget_type", sa.Enum("KPI","LINE_CHART","BAR_CHART","PIE_CHART","TABLE","METRIC_CARD","GAUGE","HEATMAP","FUNNEL","CUSTOM", name="widget_type_enum"), nullable=False, server_default="KPI"),
        sa.Column("position", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("size", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("query_config", sa.JSON(), nullable=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("refresh_interval_seconds", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dashboard_widgets_dashboard", "dashboard_widgets", ["dashboard_id"])
    op.create_index("ix_dashboard_widgets_org_widget_type", "dashboard_widgets", ["organization_id", "widget_type"])

    # ------------------------------------------------------------------
    # saved_reports
    # ------------------------------------------------------------------
    op.create_table(
        "saved_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("schedule", sa.JSON(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_generated_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_reports_org_type", "saved_reports", ["organization_id", "report_type"])
    op.create_index("ix_saved_reports_org_created_at", "saved_reports", ["organization_id", "created_at"])
    op.create_index("ix_saved_reports_org_favorite", "saved_reports", ["organization_id", "is_favorite"])
    op.create_index("ix_saved_reports_organization_id", "saved_reports", ["organization_id"])

    # ------------------------------------------------------------------
    # reports
    # ------------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("format", sa.String(20), nullable=False, server_default="PDF"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("date_range", sa.JSON(), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("file_url", sa.String(2048), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("generated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["generated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_report_id"], ["saved_reports.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_org_status", "reports", ["organization_id", "status"])
    op.create_index("ix_reports_org_type_created", "reports", ["organization_id", "report_type", "created_at"])
    op.create_index("ix_reports_expires_at", "reports", ["expires_at"])
    op.create_index("ix_reports_organization_id", "reports", ["organization_id"])
    # Now add deferred FK on saved_reports -> reports
    op.create_foreign_key(
        "fk_saved_reports_last_generated",
        "saved_reports", "reports",
        ["last_generated_report_id"], ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # forecasts
    # ------------------------------------------------------------------
    op.create_table(
        "forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False, server_default="AUTO"),
        sa.Column("horizon_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("confidence_level", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.95"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("training_date_range", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecasts_org_metric", "forecasts", ["organization_id", "metric"])
    op.create_index("ix_forecasts_org_status_created", "forecasts", ["organization_id", "status", "created_at"])
    op.create_index("ix_forecasts_organization_id", "forecasts", ["organization_id"])

    # ------------------------------------------------------------------
    # forecast_runs
    # ------------------------------------------------------------------
    op.create_table(
        "forecast_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_used", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("training_points", sa.Integer(), nullable=True),
        sa.Column("forecast_points", sa.JSON(), nullable=True),
        sa.Column("actual_points", sa.JSON(), nullable=True),
        sa.Column("accuracy", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("training_duration_seconds", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecast_runs_forecast_status", "forecast_runs", ["forecast_id", "status"])
    op.create_index("ix_forecast_runs_org_created", "forecast_runs", ["organization_id", "created_at"])
    # Add deferred FK on forecasts -> forecast_runs
    op.create_foreign_key(
        "fk_forecasts_last_run_id",
        "forecasts", "forecast_runs",
        ["last_run_id"], ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # anomalies
    # ------------------------------------------------------------------
    op.create_table(
        "anomalies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("anomaly_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(30), nullable=False, server_default="DETECTED"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("expected_value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("deviation", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("deviation_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("acknowledged_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["acknowledged_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anomalies_org_severity_status", "anomalies", ["organization_id", "severity", "status"])
    op.create_index("ix_anomalies_org_metric_detected", "anomalies", ["organization_id", "metric", "detected_at"])
    op.create_index("ix_anomalies_org_created_at", "anomalies", ["organization_id", "created_at"])
    op.create_index("ix_anomalies_organization_id", "anomalies", ["organization_id"])
    op.create_index("ix_anomalies_severity", "anomalies", ["severity"])
    op.create_index("ix_anomalies_status", "anomalies", ["status"])
    op.create_index("ix_anomalies_detected_at", "anomalies", ["detected_at"])

    # ------------------------------------------------------------------
    # integrations
    # ------------------------------------------------------------------
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Enum("SHOPIFY","WOOCOMMERCE","STRIPE","QUICKBOOKS","XERO","AMAZON","ETSY","SQUARE","CUSTOM", name="integration_provider_enum"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("CONNECTED","DISCONNECTED","ERROR","PENDING", name="integration_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("credentials_encrypted", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(2048), nullable=True),
        sa.Column("webhook_secret", sa.String(255), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("connected_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_error", sa.String(1024), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["connected_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "provider", "external_id", name="uq_integration_org_provider_external"),
    )
    op.create_index("ix_integrations_org_provider_status", "integrations", ["organization_id", "provider", "status"])
    op.create_index("ix_integrations_org_next_sync", "integrations", ["organization_id", "next_sync_at"])
    op.create_index("ix_integrations_organization_id", "integrations", ["organization_id"])
    op.create_index("ix_integrations_provider", "integrations", ["provider"])

    # ------------------------------------------------------------------
    # subscriptions
    # ------------------------------------------------------------------
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("plan", sa.Enum("FREE","BASIC","PRO","ENTERPRISE", name="subscription_plan_enum"), nullable=False, server_default="FREE"),
        sa.Column("status", sa.Enum("ACTIVE","TRIALING","PAST_DUE","CANCELED","INACTIVE", name="subscription_status_enum"), nullable=False, server_default="TRIALING"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index("ix_subscriptions_org_status_plan", "subscriptions", ["organization_id", "status", "plan"])
    op.create_index("ix_subscriptions_current_period_end", "subscriptions", ["current_period_end"])
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"], unique=True)

    # ------------------------------------------------------------------
    # usage_records
    # ------------------------------------------------------------------
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_records_subscription_id", "usage_records", ["subscription_id"])
    op.create_index("ix_usage_records_organization_id", "usage_records", ["organization_id"])
    op.create_index("ix_usage_records_metric", "usage_records", ["metric"])

    # ------------------------------------------------------------------
    # Seed default permissions (required for RBAC bootstrap)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO permissions (id, slug, name, description, category, created_at, updated_at)
        VALUES
          (gen_random_uuid(), 'org:read',          'View Organization',         'View organization details',           'admin',     now(), now()),
          (gen_random_uuid(), 'org:update',         'Update Organization',       'Update organization settings',        'admin',     now(), now()),
          (gen_random_uuid(), 'org:delete',         'Delete Organization',       'Delete the organization',             'admin',     now(), now()),
          (gen_random_uuid(), 'users:invite',       'Invite Users',              'Invite new members',                  'admin',     now(), now()),
          (gen_random_uuid(), 'users:manage',       'Manage Users',              'Update/remove members',               'admin',     now(), now()),
          (gen_random_uuid(), 'roles:manage',       'Manage Roles',              'Create/edit roles and permissions',   'admin',     now(), now()),
          (gen_random_uuid(), 'billing:manage',     'Manage Billing',            'Manage subscription and billing',     'billing',   now(), now()),
          (gen_random_uuid(), 'integrations:manage','Manage Integrations',       'Connect and configure integrations',  'admin',     now(), now()),
          (gen_random_uuid(), 'analytics:view',     'View Analytics',            'View analytics dashboards',           'analytics', now(), now()),
          (gen_random_uuid(), 'analytics:export',   'Export Analytics',          'Export analytics data',               'analytics', now(), now()),
          (gen_random_uuid(), 'dashboards:create',  'Create Dashboards',         'Create custom dashboards',            'analytics', now(), now()),
          (gen_random_uuid(), 'dashboards:manage',  'Manage Dashboards',         'Edit/delete any dashboard',           'analytics', now(), now()),
          (gen_random_uuid(), 'data:import',        'Import Data',               'Upload and import datasets',          'data',      now(), now()),
          (gen_random_uuid(), 'data:manage',        'Manage Data',               'Edit/delete datasets',                'data',      now(), now()),
          (gen_random_uuid(), 'data:export',        'Export Data',               'Export raw data',                     'data',      now(), now()),
          (gen_random_uuid(), 'reports:view',       'View Reports',              'View saved reports',                  'reports',   now(), now()),
          (gen_random_uuid(), 'reports:create',     'Create Reports',            'Generate new reports',                'reports',   now(), now()),
          (gen_random_uuid(), 'reports:manage',     'Manage Reports',            'Edit/delete any report',              'reports',   now(), now()),
          (gen_random_uuid(), 'reports:scheduled',  'Schedule Reports',          'Configure scheduled reports',         'reports',   now(), now()),
          (gen_random_uuid(), 'settings:read',      'View Settings',             'View organization settings',          'settings',  now(), now()),
          (gen_random_uuid(), 'settings:manage',    'Manage Settings',           'Update organization settings',        'settings',  now(), now()),
          (gen_random_uuid(), 'api_keys:create',    'Create API Keys',           'Create new API keys',                 'admin',     now(), now()),
          (gen_random_uuid(), 'api_keys:manage',    'Manage API Keys',           'Revoke/rotate API keys',              'admin',     now(), now())
        ON CONFLICT (slug) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("usage_records")
    op.drop_table("subscriptions")
    op.drop_table("integrations")
    op.drop_table("anomalies")
    op.execute("SELECT setval('pg_catalog.pg_sequence', 1) WHERE FALSE")  # no-op placeholder

    # Remove deferred FKs first
    op.drop_constraint("fk_forecasts_last_run_id", "forecasts", type_="foreignkey")
    op.drop_table("forecast_runs")
    op.drop_table("forecasts")
    op.drop_constraint("fk_saved_reports_last_generated", "saved_reports", type_="foreignkey")
    op.drop_table("reports")
    op.drop_table("saved_reports")
    op.drop_table("dashboard_widgets")
    op.drop_table("dashboards")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("api_keys")
    op.drop_constraint("fk_datasets_import_job_id", "datasets", type_="foreignkey")
    op.drop_table("import_jobs")
    op.drop_table("dataset_columns")
    op.drop_table("datasets")
    op.drop_table("returns")
    op.drop_table("refunds")
    op.drop_table("payments")
    op.drop_table("order_line_items")
    op.drop_table("orders")
    op.drop_table("inventory_items")
    op.drop_table("product_variants")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("addresses")
    op.drop_table("customers")
    op.drop_table("customer_segments")
    op.drop_table("organization_members")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("organizations")
    op.drop_table("users")

    # Drop enum types
    for name in [
        "user_status_enum", "organization_status_enum", "organization_size_enum",
        "default_currency_enum", "org_member_status_enum", "role_tier_enum",
        "permission_category_enum", "address_type_enum", "product_status_enum",
        "order_status_enum", "payment_status_enum", "payment_method_enum",
        "order_source_enum", "return_status_enum", "dataset_source_type_enum",
        "dataset_status_enum", "column_data_type_enum", "import_job_status_enum",
        "import_job_type_enum", "api_key_status_enum", "notification_status_enum",
        "notification_channel_enum", "widget_type_enum", "subscription_plan_enum",
        "subscription_status_enum", "integration_status_enum", "integration_provider_enum",
    ]:
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
