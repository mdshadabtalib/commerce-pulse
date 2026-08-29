from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import and_, case, cast, distinct, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ValidationError
from ..core.logging import get_logger
from ..models.customer import Address, Customer
from ..models.order import (
    Order,
    OrderLineItem,
    OrderStatus,
    PaymentStatus,
    Refund,
    Return,
    ReturnStatus,
)
from ..models.product import Category, Product
from ..schemas.analytics import (
    BreakdownItem,
    Insight,
    InsightCategory,
    InsightSeverity,
    InsightType,
    PeriodComparison,
    SalesKPIs,
    TimeSeriesPoint,
)
from ..schemas.common import DateRangeFilter, PaginatedResponse

logger = get_logger(__name__)

_PAID_STATUSES = {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}
_NON_RETURN_STATUSES = {OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _apply_date_filters(
    query,
    order_model: Any,
    date_range: DateRangeFilter | None,
    organization_id: Any,
):
    query = query.where(order_model.organization_id == organization_id)
    if date_range:
        if date_range.start_date:
            start_dt = datetime.combine(date_range.start_date, datetime.min.time())
            query = query.where(order_model.order_date >= start_dt)
        if date_range.end_date:
            end_dt = datetime.combine(date_range.end_date, datetime.max.time())
            query = query.where(order_model.order_date <= end_dt)
    return query


def _apply_order_filters(query, order_model: Any, filters: dict[str, Any]):
    if not filters:
        return query
    if filters.get("status"):
        status_list = filters["status"] if isinstance(filters["status"], list) else [filters["status"]]
        query = query.where(order_model.status.in_(status_list))
    if filters.get("payment_status"):
        ps = filters["payment_status"] if isinstance(filters["payment_status"], list) else [filters["payment_status"]]
        query = query.where(order_model.payment_status.in_(ps))
    if filters.get("source"):
        src = filters["source"] if isinstance(filters["source"], list) else [filters["source"]]
        query = query.where(order_model.source.in_(src))
    if filters.get("currency"):
        query = query.where(order_model.currency == filters["currency"])
    return query


def _date_trunc_expr(granularity: str, column: Any):
    g = granularity.lower()
    if g in ("hourly", "hour"):
        return func.date_trunc("hour", column)
    if g in ("daily", "day"):
        return func.date_trunc("day", column)
    if g in ("weekly", "week"):
        return func.date_trunc("week", column)
    if g in ("monthly", "month"):
        return func.date_trunc("month", column)
    if g in ("quarterly", "quarter"):
        return func.date_trunc("quarter", column)
    if g in ("yearly", "year"):
        return func.date_trunc("year", column)
    return func.date_trunc("day", column)


class AnalyticsService:
    async def get_sales_kpis(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
        filters: dict[str, Any] | None = None,
    ) -> SalesKPIs:
        logger.info("Computing sales KPIs", extra={"organization_id": str(organization_id)})
        filters = filters or {}

        base_order = select(Order).where(Order.organization_id == organization_id)
        base_order = _apply_date_filters(base_order, Order, date_range, organization_id)
        base_order = _apply_order_filters(base_order, Order, filters)
        paid_base = base_order.where(Order.status.in_(_PAID_STATUSES))

        order_alias = paid_base.cte("paid_orders")
        line_cte = (
            select(
                func.coalesce(func.sum(OrderLineItem.line_total), 0).label("gross_revenue"),
                func.coalesce(func.sum(OrderLineItem.quantity), 0).label("units_sold"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                OrderLineItem.cost_unit_price.isnot(None),
                                (OrderLineItem.line_total - (OrderLineItem.cost_unit_price * OrderLineItem.quantity)),
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("profit"),
                func.coalesce(func.sum(OrderLineItem.discount_amount), 0).label("discount_amount"),
                func.coalesce(
                    func.sum(
                        case(
                            (OrderLineItem.returned_quantity > 0, OrderLineItem.returned_quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("returned_units"),
            )
            .select_from(OrderLineItem)
            .where(
                OrderLineItem.organization_id == organization_id,
                OrderLineItem.order_id.in_(select(order_alias.c.id)),
            )
        )

        order_agg = (
            select(
                func.count(distinct(order_alias.c.id)).label("orders_count"),
                func.coalesce(func.sum(order_alias.c.tax_amount), 0).label("tax_amount"),
                func.coalesce(func.sum(order_alias.c.shipping_amount), 0).label("shipping_amount"),
                func.coalesce(func.sum(order_alias.c.discount_amount), 0).label("order_discount"),
            )
            .select_from(order_alias)
        )

        refund_cte = (
            select(func.coalesce(func.sum(Refund.amount), 0).label("refund_amount"))
            .select_from(Refund)
            .where(
                Refund.organization_id == organization_id,
                Refund.order_id.in_(select(order_alias.c.id)),
            )
        )

        line_res = await db.execute(line_cte)
        line_row = line_res.first() or (0, 0, 0, 0, 0)
        gross_revenue = _safe_float(line_row[0])
        units_sold = _safe_int(line_row[1])
        profit = _safe_float(line_row[2])
        line_discount = _safe_float(line_row[3])
        returned_units = _safe_int(line_row[4])

        order_res = await db.execute(order_agg)
        order_row = order_res.first() or (0, 0, 0, 0)
        orders_count = _safe_int(order_row[0])
        tax = _safe_float(order_row[1])
        shipping = _safe_float(order_row[2])
        order_discount = _safe_float(order_row[3])

        refund_res = await db.execute(refund_cte)
        refund_row = refund_res.first() or (0,)
        refund_amount = _safe_float(refund_row[0])

        total_discount = line_discount + order_discount
        net_revenue = gross_revenue + tax + shipping - total_discount - refund_amount
        aov = net_revenue / orders_count if orders_count > 0 else 0.0
        asp = gross_revenue / units_sold if units_sold > 0 else 0.0
        profit_margin = (profit / gross_revenue * 100.0) if gross_revenue > 0 else 0.0
        return_rate = (returned_units / units_sold * 100.0) if units_sold > 0 else 0.0

        return SalesKPIs(
            gross_revenue=round(gross_revenue, 2),
            net_revenue=round(net_revenue, 2),
            profit=round(profit, 2),
            profit_margin=round(profit_margin, 2),
            orders_count=orders_count,
            units_sold=units_sold,
            aov=round(aov, 2),
            asp=round(asp, 2),
            discount_amount=round(total_discount, 2),
            return_rate=round(return_rate, 2),
            refund_amount=round(refund_amount, 2),
        )

    async def get_sales_trend(
        self,
        db: AsyncSession,
        organization_id: Any,
        granularity: str = "daily",
        date_range: DateRangeFilter | None = None,
        filters: dict[str, Any] | None = None,
        metric: str = "revenue",
    ) -> list[TimeSeriesPoint]:
        logger.info(
            "Computing sales trend",
            extra={"organization_id": str(organization_id), "granularity": granularity, "metric": metric},
        )
        filters = filters or {}
        date_col = _date_trunc_expr(granularity, Order.order_date)

        order_cte = select(Order).where(Order.organization_id == organization_id)
        order_cte = _apply_date_filters(order_cte, Order, date_range, organization_id)
        order_cte = _apply_order_filters(order_cte, Order, filters)
        order_cte = order_cte.where(Order.status.in_(_PAID_STATUSES)).cte("trend_orders")

        metric_lower = metric.lower()
        if metric_lower in ("revenue", "net_revenue"):
            value_expr = func.coalesce(func.sum(order_cte.c.total_amount), 0)
        elif metric_lower in ("orders", "orders_count"):
            value_expr = func.count(distinct(order_cte.c.id))
        elif metric_lower in ("units", "units_sold"):
            value_expr = (
                select(func.coalesce(func.sum(OrderLineItem.quantity), 0))
                .where(
                    OrderLineItem.organization_id == organization_id,
                    OrderLineItem.order_id == order_cte.c.id,
                )
                .correlate(order_cte)
                .scalar_subquery()
            )
        elif metric_lower == "profit":
            value_expr = (
                select(
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    OrderLineItem.cost_unit_price.isnot(None),
                                    (
                                        OrderLineItem.line_total
                                        - (OrderLineItem.cost_unit_price * OrderLineItem.quantity)
                                    ),
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    )
                )
                .where(
                    OrderLineItem.organization_id == organization_id,
                    OrderLineItem.order_id == order_cte.c.id,
                )
                .correlate(order_cte)
                .scalar_subquery()
            )
        else:
            value_expr = func.coalesce(func.sum(order_cte.c.total_amount), 0)

        query = (
            select(
                date_col.label("bucket"),
                value_expr.label("value"),
            )
            .select_from(order_cte)
            .group_by("bucket")
            .order_by("bucket")
        )
        res = await db.execute(query)
        rows = res.all()

        points: list[TimeSeriesPoint] = []
        for bucket, value in rows:
            bucket_dt: datetime = bucket if isinstance(bucket, datetime) else datetime.combine(bucket, datetime.min.time())
            points.append(
                TimeSeriesPoint(
                    date=bucket_dt,
                    value=round(_safe_float(value), 2),
                    label=metric_lower,
                )
            )
        return points

    async def get_period_comparison(
        self,
        db: AsyncSession,
        organization_id: Any,
        current_range: DateRangeFilter,
        previous_range: DateRangeFilter,
    ) -> PeriodComparison:
        logger.info(
            "Comparing periods",
            extra={"organization_id": str(organization_id)},
        )
        current_kpis = await self.get_sales_kpis(db, organization_id, current_range)
        previous_kpis = await self.get_sales_kpis(db, organization_id, previous_range)

        fields = [
            "gross_revenue",
            "net_revenue",
            "profit",
            "profit_margin",
            "orders_count",
            "units_sold",
            "aov",
            "asp",
            "discount_amount",
            "return_rate",
            "refund_amount",
        ]
        growth_rates: dict[str, float] = {}
        for f in fields:
            cur = getattr(current_kpis, f, 0)
            prev = getattr(previous_kpis, f, 0)
            if prev in (0, 0.0):
                growth_rates[f] = 0.0 if cur == prev else float("inf") if cur > 0 else float("-inf")
            else:
                growth_rates[f] = round(((cur - prev) / prev) * 100.0, 2)

        return PeriodComparison(
            current_period=current_kpis,
            previous_period=previous_kpis,
            growth_rates=growth_rates,
        )

    async def get_category_breakdown(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
    ) -> list[BreakdownItem]:
        logger.info(
            "Computing category breakdown",
            extra={"organization_id": str(organization_id)},
        )
        order_cte = select(Order.id).where(Order.organization_id == organization_id)
        order_cte = _apply_date_filters(order_cte, Order, date_range, organization_id)
        order_cte = order_cte.where(Order.status.in_(_PAID_STATUSES)).cte("cat_orders")

        query = (
            select(
                func.coalesce(Category.name, "Uncategorized").label("name"),
                func.coalesce(func.sum(OrderLineItem.line_total), 0).label("value"),
            )
            .select_from(OrderLineItem)
            .outerjoin(Product, Product.id == OrderLineItem.product_id)
            .outerjoin(Category, Category.id == Product.category_id)
            .where(
                OrderLineItem.organization_id == organization_id,
                OrderLineItem.order_id.in_(select(order_cte.c.id)),
            )
            .group_by(Category.name)
            .order_by(func.sum(OrderLineItem.line_total).desc())
        )
        res = await db.execute(query)
        rows = res.all()
        total = sum(_safe_float(r[1]) for r in rows)
        items: list[BreakdownItem] = []
        for name, value in rows:
            v = _safe_float(value)
            pct = (v / total * 100.0) if total > 0 else 0.0
            items.append(BreakdownItem(name=name or "Uncategorized", value=round(v, 2), percentage=round(pct, 2)))
        return items

    async def get_product_performance(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[dict[str, Any]]:
        logger.info(
            "Computing product performance",
            extra={"organization_id": str(organization_id), "limit": limit},
        )
        order_cte = select(Order.id).where(Order.organization_id == organization_id)
        order_cte = _apply_date_filters(order_cte, Order, date_range, organization_id)
        order_cte = order_cte.where(Order.status.in_(_PAID_STATUSES)).cte("perf_orders")

        return_cte = (
            select(
                Return.line_item_id,
                func.coalesce(func.sum(Return.quantity), 0).label("return_qty"),
            )
            .select_from(Return)
            .where(
                Return.organization_id == organization_id,
                Return.status.in_(
                    {ReturnStatus.REQUESTED, ReturnStatus.APPROVED, ReturnStatus.SHIPPED, ReturnStatus.RECEIVED, ReturnStatus.COMPLETED}
                ),
            )
            .group_by(Return.line_item_id)
            .cte("return_items")
        )

        base_query = (
            select(
                Product.id,
                Product.sku,
                Product.name,
                func.coalesce(func.sum(OrderLineItem.line_total), 0).label("revenue"),
                func.coalesce(func.sum(OrderLineItem.quantity), 0).label("units"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                OrderLineItem.cost_unit_price.isnot(None),
                                (
                                    OrderLineItem.line_total
                                    - (OrderLineItem.cost_unit_price * OrderLineItem.quantity)
                                ),
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("profit"),
                func.coalesce(func.sum(return_cte.c.return_qty), 0).label("returned"),
            )
            .select_from(OrderLineItem)
            .join(Product, Product.id == OrderLineItem.product_id)
            .outerjoin(return_cte, return_cte.c.line_item_id == OrderLineItem.id)
            .where(
                OrderLineItem.organization_id == organization_id,
                OrderLineItem.order_id.in_(select(order_cte.c.id)),
            )
            .group_by(Product.id, Product.sku, Product.name)
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_res = await db.execute(count_query)
        total = _safe_int(total_res.scalar())

        query = base_query.order_by(func.sum(OrderLineItem.line_total).desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        rows = res.all()

        items: list[dict[str, Any]] = []
        for pid, sku, name, revenue, units, profit, returned in rows:
            u = _safe_int(units)
            ret = _safe_int(returned)
            return_rate = (ret / u * 100.0) if u > 0 else 0.0
            items.append(
                {
                    "product_id": str(pid),
                    "sku": sku,
                    "name": name,
                    "revenue": round(_safe_float(revenue), 2),
                    "units": u,
                    "profit": round(_safe_float(profit), 2),
                    "returned_units": ret,
                    "return_rate": round(return_rate, 2),
                }
            )

        per_page = limit if limit > 0 else settings.PAGE_SIZE_DEFAULT
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=(offset // per_page) + 1 if per_page > 0 else 1,
            per_page=per_page,
            total_pages=total_pages,
        )

    async def get_geographic_breakdown(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
    ) -> list[BreakdownItem]:
        logger.info(
            "Computing geographic breakdown",
            extra={"organization_id": str(organization_id)},
        )
        order_cte = select(Order).where(Order.organization_id == organization_id)
        order_cte = _apply_date_filters(order_cte, Order, date_range, organization_id)
        order_cte = order_cte.where(Order.status.in_(_PAID_STATUSES)).cte("geo_orders")

        query = (
            select(
                func.coalesce(Address.country_code, "UNKNOWN").label("country"),
                func.coalesce(Address.state, "").label("state"),
                func.count(distinct(order_cte.c.id)).label("orders"),
                func.coalesce(func.sum(order_cte.c.total_amount), 0).label("revenue"),
            )
            .select_from(order_cte)
            .outerjoin(Address, Address.id == order_cte.c.shipping_address_id)
            .group_by(Address.country_code, Address.state)
            .order_by(func.sum(order_cte.c.total_amount).desc())
        )
        res = await db.execute(query)
        rows = res.all()
        total_rev = sum(_safe_float(r[3]) for r in rows)

        items: list[BreakdownItem] = []
        for country, state, orders, revenue in rows:
            r = _safe_float(revenue)
            o = _safe_int(orders)
            aov = r / o if o > 0 else 0.0
            label = f"{country or 'Unknown'}" + (f" - {state}" if state else "")
            pct = (r / total_rev * 100.0) if total_rev > 0 else 0.0
            items.append(
                BreakdownItem(
                    name=label,
                    value=round(r, 2),
                    percentage=round(pct, 2),
                )
            )
            _ = aov
        return items

    async def get_customer_kpis(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Computing customer KPIs",
            extra={"organization_id": str(organization_id)},
        )
        first_order_cte = (
            select(
                Order.customer_id,
                func.min(Order.order_date).label("first_date"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.status.in_(_PAID_STATUSES),
                Order.customer_id.isnot(None),
            )
            .group_by(Order.customer_id)
            .cte("first_order")
        )

        order_in_range = (
            select(Order.customer_id, Order.id, Order.total_amount, Order.order_date)
            .where(Order.organization_id == organization_id, Order.status.in_(_PAID_STATUSES))
        )
        if date_range:
            if date_range.start_date:
                order_in_range = order_in_range.where(
                    Order.order_date >= datetime.combine(date_range.start_date, datetime.min.time())
                )
            if date_range.end_date:
                order_in_range = order_in_range.where(
                    Order.order_date <= datetime.combine(date_range.end_date, datetime.max.time())
                )
        order_cte = order_in_range.cte("period_orders")

        new_customers_q = select(func.count(distinct(first_order_cte.c.customer_id))).select_from(first_order_cte)
        if date_range and date_range.start_date:
            new_customers_q = new_customers_q.where(
                first_order_cte.c.first_date >= datetime.combine(date_range.start_date, datetime.min.time())
            )
        if date_range and date_range.end_date:
            new_customers_q = new_customers_q.where(
                first_order_cte.c.first_date <= datetime.combine(date_range.end_date, datetime.max.time())
            )
        new_res = await db.execute(new_customers_q)
        new_customers = _safe_int(new_res.scalar())

        period_cust_q = select(func.count(distinct(order_cte.c.customer_id))).where(order_cte.c.customer_id.isnot(None))
        period_res = await db.execute(period_cust_q)
        total_period_customers = _safe_int(period_res.scalar())
        returning_customers = max(0, total_period_customers - new_customers)

        orders_per_cust_q = (
            select(func.count(order_cte.c.id), order_cte.c.customer_id)
            .where(order_cte.c.customer_id.isnot(None))
            .group_by(order_cte.c.customer_id)
        )
        opc_res = await db.execute(orders_per_cust_q)
        order_counts = [_safe_int(r[0]) for r in opc_res.all()]
        if order_counts:
            arr = np.array(order_counts, dtype=float)
            repeat_rate = float(np.mean(arr > 1)) * 100.0
            purchase_freq = float(np.mean(arr))
        else:
            repeat_rate = 0.0
            purchase_freq = 0.0

        spend_q = (
            select(func.coalesce(func.sum(order_cte.c.total_amount), 0))
            .where(order_cte.c.customer_id.isnot(None))
        )
        spend_res = await db.execute(spend_q)
        total_spend = _safe_float(spend_res.scalar())
        avg_customer_spend = total_spend / total_period_customers if total_period_customers > 0 else 0.0

        return {
            "new_customers": new_customers,
            "returning_customers": returning_customers,
            "total_active_customers": total_period_customers,
            "repeat_rate": round(repeat_rate, 2),
            "avg_customer_spend": round(avg_customer_spend, 2),
            "purchase_frequency": round(purchase_freq, 2),
        }

    async def get_cohort_analysis(
        self,
        db: AsyncSession,
        organization_id: Any,
    ) -> dict[str, Any]:
        logger.info("Running cohort analysis", extra={"organization_id": str(organization_id)})

        first_order_q = (
            select(
                Order.customer_id,
                func.date_trunc("month", func.min(Order.order_date)).label("cohort_month"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.status.in_(_PAID_STATUSES),
                Order.customer_id.isnot(None),
            )
            .group_by(Order.customer_id)
            .cte("customer_cohorts")
        )

        activity_q = (
            select(
                first_order_q.c.cohort_month,
                func.date_trunc("month", Order.order_date).label("activity_month"),
                func.count(distinct(Order.customer_id)).label("active_customers"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            )
            .select_from(Order)
            .join(first_order_q, first_order_q.c.customer_id == Order.customer_id)
            .where(
                Order.organization_id == organization_id,
                Order.status.in_(_PAID_STATUSES),
                Order.customer_id.isnot(None),
            )
            .group_by(first_order_q.c.cohort_month, "activity_month")
            .order_by(first_order_q.c.cohort_month, "activity_month")
        )

        cohort_sizes_q = (
            select(
                first_order_q.c.cohort_month,
                func.count(first_order_q.c.customer_id).label("size"),
            )
            .group_by(first_order_q.c.cohort_month)
        )

        size_res = await db.execute(cohort_sizes_q)
        cohort_sizes = {r[0]: _safe_int(r[1]) for r in size_res.all()}

        act_res = await db.execute(activity_q)
        rows = act_res.all()

        df_rows = []
        for cohort_month, activity_month, active, revenue in rows:
            size = cohort_sizes.get(cohort_month, 0)
            if cohort_month and activity_month:
                period_num = (
                    (activity_month.year - cohort_month.year) * 12 + (activity_month.month - cohort_month.month)
                )
            else:
                period_num = 0
            retention_pct = (active / size * 100.0) if size > 0 else 0.0
            df_rows.append(
                {
                    "cohort": cohort_month.isoformat() if cohort_month else None,
                    "cohort_size": size,
                    "period": period_num,
                    "activity_month": activity_month.isoformat() if activity_month else None,
                    "active_customers": _safe_int(active),
                    "retention_pct": round(retention_pct, 2),
                    "revenue": round(_safe_float(revenue), 2),
                }
            )
        return {"retention_matrix": df_rows, "cohorts": sorted(list({r["cohort"] for r in df_rows}))}

    async def get_rfm_analysis(
        self,
        db: AsyncSession,
        organization_id: Any,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        logger.info("Computing RFM analysis", extra={"organization_id": str(organization_id)})
        as_of = as_of or datetime.now()

        rfm_q = (
            select(
                Customer.id,
                Customer.email,
                Customer.first_name,
                Customer.last_name,
                func.max(Order.order_date).label("last_order"),
                func.count(distinct(Order.id)).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spend"),
            )
            .select_from(Customer)
            .outerjoin(
                Order,
                and_(
                    Order.customer_id == Customer.id,
                    Order.organization_id == organization_id,
                    Order.status.in_(_PAID_STATUSES),
                ),
            )
            .where(Customer.organization_id == organization_id)
            .group_by(Customer.id)
        )
        res = await db.execute(rfm_q)
        rows = res.all()

        if not rows:
            return {"customers": [], "segments": []}

        df = pd.DataFrame(
            [
                {
                    "customer_id": str(r[0]),
                    "email": r[1],
                    "first_name": r[2],
                    "last_name": r[3],
                    "last_order": r[4],
                    "frequency": _safe_int(r[5]),
                    "monetary": _safe_float(r[6]),
                }
                for r in rows
            ]
        )

        df["last_order"] = pd.to_datetime(df["last_order"])
        df["recency_days"] = (as_of - df["last_order"]).dt.total_seconds() / 86400.0
        df["recency_days"] = df["recency_days"].fillna(9999)

        def _score(series: pd.Series, pcts: tuple[float, ...] = (20, 40, 60, 80), invert: bool = False) -> pd.Series:
            values = series.replace([np.inf, -np.inf], np.nan).dropna()
            if len(values) == 0:
                return pd.Series([3] * len(series), index=series.index)
            q = np.percentile(values, list(pcts))
            if invert:
                bins = [-np.inf, q[0], q[1], q[2], q[3], np.inf]
                labels = [5, 4, 3, 2, 1]
            else:
                bins = [-np.inf, q[0], q[1], q[2], q[3], np.inf]
                labels = [1, 2, 3, 4, 5]
            return pd.cut(series, bins=bins, labels=labels, include_lowest=True).astype(int)

        df["r_score"] = _score(df["recency_days"], invert=True)
        df["f_score"] = _score(df["frequency"].astype(float))
        df["m_score"] = _score(df["monetary"].astype(float))
        df["rfm_score"] = df["r_score"] + df["f_score"] + df["m_score"]

        def _assign_segment(row: pd.Series) -> str:
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            if r >= 3 and f >= 3 and m >= 3:
                return "Loyal Customers"
            if r >= 4 and f <= 2 and m <= 2:
                return "New Customers"
            if r <= 2 and f >= 3 and m >= 3:
                return "At Risk"
            if r <= 2 and f <= 2 and m <= 2:
                return "Lost"
            if r >= 3 and f >= 4 and m >= 4:
                return "Potential Loyalists"
            if r == 5 and (f == 1 or m == 1):
                return "Promising"
            if r <= 2 and (f >= 1 or m >= 1):
                return "Can't Lose Them"
            if r >= 3 and f <= 2 and m >= 3:
                return "Need Attention"
            return "Others"

        df["segment"] = df.apply(_assign_segment, axis=1)

        customers_out = []
        for _, row in df.iterrows():
            last_order_val = None
            if pd.notna(row["last_order"]):
                if isinstance(row["last_order"], pd.Timestamp):
                    last_order_val = row["last_order"].isoformat()
                else:
                    last_order_val = str(row["last_order"])
            customers_out.append(
                {
                    "customer_id": row["customer_id"],
                    "email": row["email"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "recency_days": round(float(row["recency_days"]), 1),
                    "frequency": int(row["frequency"]),
                    "monetary": round(float(row["monetary"]), 2),
                    "r_score": int(row["r_score"]),
                    "f_score": int(row["f_score"]),
                    "m_score": int(row["m_score"]),
                    "rfm_score": int(row["rfm_score"]),
                    "segment": row["segment"],
                    "last_order": last_order_val,
                }
            )

        seg_df = df.groupby("segment").agg(
            customers=("customer_id", "count"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
        ).reset_index()

        total_cust = len(df)
        segments_out = []
        for _, row in seg_df.iterrows():
            segments_out.append(
                {
                    "segment": row["segment"],
                    "customers": int(row["customers"]),
                    "percentage": round(float(row["customers"]) / total_cust * 100.0, 2) if total_cust else 0.0,
                    "avg_recency_days": round(float(row["avg_recency"]), 1),
                    "avg_frequency": round(float(row["avg_frequency"]), 2),
                    "avg_monetary": round(float(row["avg_monetary"]), 2),
                    "total_revenue": round(float(row["total_revenue"]), 2),
                }
            )

        return {"customers": customers_out, "segments": segments_out}

    async def get_product_profitability_matrix(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Computing product profitability matrix",
            extra={"organization_id": str(organization_id)},
        )
        order_cte = select(Order.id).where(Order.organization_id == organization_id)
        order_cte = _apply_date_filters(order_cte, Order, date_range, organization_id)
        order_cte = order_cte.where(Order.status.in_(_PAID_STATUSES)).cte("prof_orders")

        query = (
            select(
                Product.id,
                Product.sku,
                Product.name,
                func.coalesce(func.sum(OrderLineItem.line_total), 0).label("revenue"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                OrderLineItem.cost_unit_price.isnot(None),
                                (
                                    OrderLineItem.line_total
                                    - (OrderLineItem.cost_unit_price * OrderLineItem.quantity)
                                ),
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("profit"),
            )
            .select_from(OrderLineItem)
            .join(Product, Product.id == OrderLineItem.product_id)
            .where(
                OrderLineItem.organization_id == organization_id,
                OrderLineItem.order_id.in_(select(order_cte.c.id)),
            )
            .group_by(Product.id, Product.sku, Product.name)
        )
        res = await db.execute(query)
        rows = res.all()
        if not rows:
            return {"quadrants": {}, "products": []}

        df = pd.DataFrame(
            [
                {
                    "product_id": str(r[0]),
                    "sku": r[1],
                    "name": r[2],
                    "revenue": _safe_float(r[3]),
                    "profit": _safe_float(r[4]),
                }
                for r in rows
            ]
        )
        df["margin_pct"] = np.where(df["revenue"] > 0, df["profit"] / df["revenue"] * 100.0, 0.0)

        rev_median = float(df["revenue"].median()) if len(df) else 0.0
        margin_median = float(df["margin_pct"].median()) if len(df) else 0.0

        def _quadrant(row: pd.Series) -> str:
            high_rev = row["revenue"] >= rev_median
            high_margin = row["margin_pct"] >= margin_median
            if high_rev and high_margin:
                return "Stars (High Rev / High Margin)"
            if high_rev and not high_margin:
                return "Cash Cows (High Rev / Low Margin)"
            if not high_rev and high_margin:
                return "Question Marks (Low Rev / High Margin)"
            return "Dogs (Low Rev / Low Margin)"

        df["quadrant"] = df.apply(_quadrant, axis=1)

        products_out = []
        for _, row in df.iterrows():
            products_out.append(
                {
                    "product_id": row["product_id"],
                    "sku": row["sku"],
                    "name": row["name"],
                    "revenue": round(float(row["revenue"]), 2),
                    "profit": round(float(row["profit"]), 2),
                    "margin_pct": round(float(row["margin_pct"]), 2),
                    "quadrant": row["quadrant"],
                }
            )

        quad_counts = df.groupby("quadrant").agg(
            products=("product_id", "count"),
            total_revenue=("revenue", "sum"),
            total_profit=("profit", "sum"),
        ).to_dict("index")

        quad_out = {}
        for k, v in quad_counts.items():
            quad_out[k] = {
                "products": int(v["products"]),
                "total_revenue": round(float(v["total_revenue"]), 2),
                "total_profit": round(float(v["total_profit"]), 2),
            }

        return {
            "quadrants": quad_out,
            "products": products_out,
            "thresholds": {
                "revenue_median": round(rev_median, 2),
                "margin_median_pct": round(margin_median, 2),
            },
        }

    async def generate_insights(
        self,
        db: AsyncSession,
        organization_id: Any,
        date_range: DateRangeFilter,
    ) -> list[Insight]:
        logger.info("Generating insights", extra={"organization_id": str(organization_id)})
        insights: list[Insight] = []

        end = date_range.end_date or date.today()
        start = date_range.start_date or (end - timedelta(days=30))
        current_range = DateRangeFilter(start_date=start, end_date=end)
        days = (end - start).days or 30
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days)
        previous_range = DateRangeFilter(start_date=prev_start, end_date=prev_end)

        try:
            comparison = await self.get_period_comparison(db, organization_id, current_range, previous_range)
            cur = comparison.current_period
            prev = comparison.previous_period
            growth = comparison.growth_rates

            rev_change = growth.get("net_revenue", 0.0)
            orders_change = growth.get("orders_count", 0.0)
            aov_change = growth.get("aov", 0.0)

            if abs(rev_change) >= 20:
                direction = "increased" if rev_change > 0 else "decreased"
                sev = InsightSeverity.HIGH if abs(rev_change) >= 50 else InsightSeverity.MEDIUM
                insights.append(
                    Insight(
                        category=InsightCategory.SALES,
                        type=InsightType.OBSERVATION,
                        title=f"Net revenue {direction} {abs(rev_change):.1f}%",
                        description=(
                            f"Net revenue {direction} from ${prev.net_revenue:,.2f} in the prior "
                            f"period to ${cur.net_revenue:,.2f} in the current period ({days} days)."
                        ),
                        severity=sev,
                        evidence={
                            "current_net_revenue": cur.net_revenue,
                            "previous_net_revenue": prev.net_revenue,
                            "change_pct": rev_change,
                            "period_days": days,
                        },
                        confidence=0.95,
                    )
                )

            if abs(orders_change) >= 15:
                direction = "up" if orders_change > 0 else "down"
                insights.append(
                    Insight(
                        category=InsightCategory.SALES,
                        type=InsightType.STATISTICAL,
                        title=f"Order count is {direction} {abs(orders_change):.1f}%",
                        description=(
                            f"Paid orders moved from {prev.orders_count} to {cur.orders_count} "
                            f"({direction} {abs(orders_change):.1f}%)."
                        ),
                        severity=InsightSeverity.MEDIUM if abs(orders_change) >= 30 else InsightSeverity.LOW,
                        evidence={
                            "current_orders": cur.orders_count,
                            "previous_orders": prev.orders_count,
                            "change_pct": orders_change,
                        },
                        confidence=0.9,
                    )
                )

            if cur.return_rate >= 15:
                insights.append(
                    Insight(
                        category=InsightCategory.PRODUCT,
                        type=InsightType.RECOMMENDATION,
                        title=f"High return rate: {cur.return_rate:.1f}%",
                        description=(
                            f"Return rate is {cur.return_rate:.1f}% across {cur.units_sold} units sold. "
                            "Investigate product quality, sizing, and listing accuracy."
                        ),
                        severity=InsightSeverity.HIGH if cur.return_rate >= 25 else InsightSeverity.MEDIUM,
                        evidence={
                            "return_rate": cur.return_rate,
                            "units_sold": cur.units_sold,
                            "threshold_recommended": 10.0,
                        },
                        confidence=0.85,
                    )
                )

            if cur.profit_margin <= 0 and cur.gross_revenue > 0:
                insights.append(
                    Insight(
                        category=InsightCategory.FINANCIAL,
                        type=InsightType.FACT,
                        title="Unprofitable sales period",
                        description=(
                            f"Gross revenue ${cur.gross_revenue:,.2f} yielded ${cur.profit:,.2f} in "
                            f"profit ({cur.profit_margin:.1f}% margin). Review pricing and COGS."
                        ),
                        severity=InsightSeverity.HIGH,
                        evidence={
                            "gross_revenue": cur.gross_revenue,
                            "profit": cur.profit,
                            "profit_margin": cur.profit_margin,
                        },
                        confidence=0.95,
                    )
                )

            if aov_change <= -10 and cur.orders_count > prev.orders_count:
                insights.append(
                    Insight(
                        category=InsightCategory.MARKETING,
                        type=InsightType.HYPOTHESIS,
                        title="Lower AOV with more orders suggests discount-driven mix",
                        description=(
                            f"AOV fell {abs(aov_change):.1f}% while orders rose {orders_change:.1f}%. "
                            "This pattern often indicates promotional mix or lower-tier product mix. "
                            "Cross-check with coupon/discount breakdown."
                        ),
                        severity=InsightSeverity.LOW,
                        evidence={
                            "aov_current": cur.aov,
                            "aov_previous": prev.aov,
                            "orders_current": cur.orders_count,
                            "orders_previous": prev.orders_count,
                            "discount_amount": cur.discount_amount,
                        },
                        confidence=0.6,
                    )
                )
        except Exception as exc:
            logger.warning("Failed to build sales insights", exc_info=True, extra={"error": str(exc)})

        try:
            cust_kpis = await self.get_customer_kpis(db, organization_id, current_range)
            repeat_rate = cust_kpis.get("repeat_rate", 0.0)
            if repeat_rate < 20 and cust_kpis.get("total_active_customers", 0) >= 10:
                insights.append(
                    Insight(
                        category=InsightCategory.CUSTOMER,
                        type=InsightType.RECOMMENDATION,
                        title="Low repeat purchase rate",
                        description=(
                            f"Only {repeat_rate:.1f}% of active customers purchased more than once in the period. "
                            "Consider loyalty programs, post-purchase campaigns, or replenishment reminders."
                        ),
                        severity=InsightSeverity.MEDIUM,
                        evidence={
                            "repeat_rate": repeat_rate,
                            "active_customers": cust_kpis.get("total_active_customers"),
                            "benchmark": 30.0,
                        },
                        confidence=0.8,
                    )
                )
        except Exception as exc:
            logger.warning("Failed to build customer insights", exc_info=True, extra={"error": str(exc)})

        try:
            cats = await self.get_category_breakdown(db, organization_id, current_range)
            if len(cats) >= 2:
                top = cats[0]
                if top.percentage and top.percentage >= 60:
                    insights.append(
                        Insight(
                            category=InsightCategory.PRODUCT,
                            type=InsightType.OBSERVATION,
                            title=f"Category concentration: {top.name} drives {top.percentage:.1f}% of revenue",
                            description=(
                                f"Category {top.name} generated ${top.value:,.2f}, representing "
                                f"{top.percentage:.1f}% of total category revenue. Diversify to reduce risk."
                            ),
                            severity=InsightSeverity.MEDIUM if top.percentage >= 75 else InsightSeverity.LOW,
                            evidence={
                                "category": top.name,
                                "revenue": top.value,
                                "percentage": top.percentage,
                                "categories_count": len(cats),
                            },
                            confidence=0.9,
                        )
                    )
        except Exception as exc:
            logger.warning("Failed to build category insights", exc_info=True, extra={"error": str(exc)})

        insights.sort(key=lambda i: (i.severity.value, i.confidence), reverse=True)
        return insights
