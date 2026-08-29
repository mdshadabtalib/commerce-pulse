"""Data ingestion service — file upload, validation, schema detection, and ETL pipeline.

Pipeline:
    Upload file → Compute checksum (dedup) → Detect schema → Validate rows
    → Persist validated rows → Update dataset status → Record audit log

Supported formats: CSV, Excel (.xlsx/.xls), JSON (array or records)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ValidationError
from ..core.logging import get_logger
from ..models.dataset import (
    ColumnDataType,
    DatasetSourceType,
    DatasetStatus,
    ImportJobStatus,
    ImportJobType,
)
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.organization_repository import OrganizationRepository
from ..schemas.dataset import DatasetValidationResponse, ColumnMappingInfo

logger = get_logger(__name__)

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/json",
    "text/json",
}

# ---------------------------------------------------------------------------
# Standard field mappings — heuristics to map column names to domain fields
# ---------------------------------------------------------------------------
_FIELD_HINTS: dict[str, str] = {
    # Orders
    "order_id": "order.external_id",
    "order_number": "order.order_number",
    "order_date": "order.order_date",
    "purchase_date": "order.order_date",
    "date": "order.order_date",
    "status": "order.status",
    "order_status": "order.status",
    "total": "order.total_amount",
    "total_amount": "order.total_amount",
    "order_total": "order.total_amount",
    "revenue": "order.total_amount",
    "subtotal": "order.subtotal",
    "discount": "order.discount_amount",
    "discount_amount": "order.discount_amount",
    "tax": "order.tax_amount",
    "tax_amount": "order.tax_amount",
    "shipping": "order.shipping_amount",
    "currency": "order.currency",
    "payment_method": "order.payment_method",
    # Customers
    "customer_id": "customer.external_id",
    "customer_email": "customer.email",
    "email": "customer.email",
    "customer_name": "customer.first_name",
    "first_name": "customer.first_name",
    "last_name": "customer.last_name",
    "phone": "customer.phone",
    # Products
    "product_id": "product.external_id",
    "product_name": "product.name",
    "product": "product.name",
    "sku": "product.sku",
    "category": "product.category",
    "brand": "product.brand",
    "price": "order_line_item.unit_price",
    "unit_price": "order_line_item.unit_price",
    "quantity": "order_line_item.quantity",
    "qty": "order_line_item.quantity",
    "cost": "order_line_item.cost_unit_price",
    "cost_price": "order_line_item.cost_unit_price",
    # Geography
    "country": "address.country_code",
    "country_code": "address.country_code",
    "state": "address.state",
    "city": "address.city",
    "postal_code": "address.postal_code",
    "zip": "address.postal_code",
}


def _slugify_col(name: str) -> str:
    """Normalise a column header for hint matching."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _detect_dtype(samples: list[Any]) -> ColumnDataType:
    """Infer the most likely data type from a list of sample values."""
    non_null = [s for s in samples if s is not None and str(s).strip() not in ("", "null", "NULL", "None")]
    if not non_null:
        return ColumnDataType.UNKNOWN

    # Try date/datetime
    date_patterns = [
        r"^\d{4}-\d{2}-\d{2}$",
        r"^\d{2}/\d{2}/\d{4}$",
        r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}",
    ]
    dt_count = 0
    for s in non_null[:20]:
        sv = str(s).strip()
        for pat in date_patterns:
            if re.match(pat, sv):
                dt_count += 1
                break
    if dt_count / max(len(non_null[:20]), 1) > 0.8:
        has_time = any("T" in str(s) or " " in str(s).strip() for s in non_null[:5])
        return ColumnDataType.DATETIME if has_time else ColumnDataType.DATE

    # Try integer
    int_ok = 0
    for s in non_null[:20]:
        try:
            v = str(s).strip().replace(",", "")
            int(v)
            int_ok += 1
        except ValueError:
            pass
    if int_ok / max(len(non_null[:20]), 1) > 0.9:
        return ColumnDataType.INTEGER

    # Try float / currency
    float_ok, cur_ok = 0, 0
    for s in non_null[:20]:
        sv = str(s).strip().lstrip("$€£₹").replace(",", "")
        if sv != str(s).strip():
            cur_ok += 1
        try:
            float(sv)
            float_ok += 1
        except ValueError:
            pass
    if float_ok / max(len(non_null[:20]), 1) > 0.9:
        return ColumnDataType.CURRENCY if cur_ok > 2 else ColumnDataType.FLOAT

    # Email heuristic
    email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    if all(email_re.match(str(s).strip()) for s in non_null[:5] if s):
        return ColumnDataType.EMAIL

    return ColumnDataType.STRING


def _compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_csv(data: bytes) -> tuple[list[str], list[list[Any]]]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    headers = [h.strip() for h in rows[0]]
    return headers, rows[1:]


def _parse_excel(data: bytes) -> tuple[list[str], list[list[Any]]]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows = [[cell.value for cell in row] for row in ws.iter_rows()]
        if not rows:
            return [], []
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
        return headers, rows[1:]
    except Exception as exc:
        raise ValidationError(message=f"Failed to parse Excel file: {exc}") from exc


def _parse_json(data: bytes) -> tuple[list[str], list[list[Any]]]:
    try:
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, list):
            if not payload:
                return [], []
            if isinstance(payload[0], dict):
                headers = list(payload[0].keys())
                rows = [[row.get(h) for h in headers] for row in payload]
                return headers, rows
        raise ValidationError(message="JSON must be an array of objects.")
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(message=f"Invalid JSON: {exc}") from exc


def _validate_row(
    headers: list[str],
    row: list[Any],
    row_idx: int,
    column_types: dict[str, ColumnDataType],
) -> list[dict[str, Any]]:
    """Validate a single row. Returns list of error dicts (empty = clean)."""
    errors: list[dict[str, Any]] = []
    for i, (header, value) in enumerate(zip(headers, row)):
        dtype = column_types.get(header, ColumnDataType.UNKNOWN)
        if value is None or str(value).strip() in ("", "null", "NULL", "None"):
            continue  # nulls are collected as completeness issue, not hard error
        sv = str(value).strip()
        if dtype == ColumnDataType.INTEGER:
            try:
                int(sv.replace(",", ""))
            except ValueError:
                errors.append({"row": row_idx, "column": header, "value": sv, "error": "Expected integer"})
        elif dtype in (ColumnDataType.FLOAT, ColumnDataType.CURRENCY):
            try:
                Decimal(sv.lstrip("$€£₹").replace(",", ""))
            except InvalidOperation:
                errors.append({"row": row_idx, "column": header, "value": sv, "error": "Expected numeric value"})
        elif dtype in (ColumnDataType.DATE, ColumnDataType.DATETIME):
            if not re.match(
                r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", sv
            ):
                errors.append({"row": row_idx, "column": header, "value": sv, "error": "Expected date"})
    return errors


class IngestionService:
    """Handles file ingestion: parsing, validation, schema detection, and DB import."""

    def __init__(self) -> None:
        self._dataset_repo: DatasetRepository | None = None

    def _get_dataset_repo(self) -> DatasetRepository:
        from ..models.dataset import Dataset
        return DatasetRepository(Dataset)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_upload(
        self,
        filename: str,
        content_type: str | None,
        file_size: int,
    ) -> DatasetSourceType:
        """Validate uploaded file metadata before reading content. Returns detected source type."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                message=f"File type '{ext}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                details={"extension": ext},
            )
        if content_type and content_type.split(";")[0].strip() not in ALLOWED_MIME_TYPES:
            logger.warning("Unexpected MIME type: %s for extension %s", content_type, ext)

        if file_size > MAX_UPLOAD_BYTES:
            raise ValidationError(
                message=f"File size exceeds maximum of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                details={"size_bytes": file_size, "max_bytes": MAX_UPLOAD_BYTES},
            )

        type_map = {
            ".csv": DatasetSourceType.CSV,
            ".json": DatasetSourceType.JSON,
            ".xlsx": DatasetSourceType.EXCEL,
            ".xls": DatasetSourceType.EXCEL,
        }
        return type_map[ext]

    def parse_file(
        self,
        data: bytes,
        source_type: DatasetSourceType,
    ) -> tuple[list[str], list[list[Any]]]:
        """Parse raw bytes into (headers, rows)."""
        if source_type == DatasetSourceType.CSV:
            return _parse_csv(data)
        elif source_type == DatasetSourceType.EXCEL:
            return _parse_excel(data)
        elif source_type == DatasetSourceType.JSON:
            return _parse_json(data)
        raise ValidationError(message=f"Unsupported source type: {source_type}")

    def detect_schema(
        self,
        headers: list[str],
        rows: list[list[Any]],
        *,
        sample_size: int = 100,
    ) -> list[ColumnMappingInfo]:
        """Detect column types and produce mapping suggestions."""
        sample = rows[:sample_size]
        mappings: list[ColumnMappingInfo] = []
        for i, header in enumerate(headers):
            col_values = [row[i] if i < len(row) else None for row in sample]
            dtype = _detect_dtype(col_values)
            slug = _slugify_col(header)
            mapped_to = _FIELD_HINTS.get(slug)
            non_null = [v for v in col_values if v is not None and str(v).strip() not in ("", "null")]
            mappings.append(
                ColumnMappingInfo(
                    source_column=header,
                    target_entity=mapped_to.split(".")[0] if mapped_to else "",
                    target_field=mapped_to.split(".")[1] if mapped_to and "." in mapped_to else "",
                    data_type=dtype.value,
                    sample_count=len(non_null),
                )
            )
        return mappings

    def validate_data(
        self,
        headers: list[str],
        rows: list[list[Any]],
        column_mappings: list[ColumnMappingInfo],
    ) -> DatasetValidationResponse:
        """Run data quality checks and return a validation report."""
        col_types = {m.source_column: ColumnDataType(m.data_type) for m in column_mappings}
        total = len(rows)
        errors: list[dict[str, Any]] = []
        null_counts: dict[str, int] = {h: 0 for h in headers}
        seen_rows: set[str] = set()
        duplicate_count = 0

        for idx, row in enumerate(rows, start=2):  # row 1 = header
            # Null check
            for i, header in enumerate(headers):
                v = row[i] if i < len(row) else None
                if v is None or str(v).strip() in ("", "null", "NULL", "None"):
                    null_counts[header] = null_counts.get(header, 0) + 1

            # Duplicate check (simple hash of full row)
            row_hash = hashlib.md5(
                "|".join(str(v) if v is not None else "" for v in row).encode()
            ).hexdigest()
            if row_hash in seen_rows:
                duplicate_count += 1
            else:
                seen_rows.add(row_hash)

            # Type validation
            row_errors = _validate_row(headers, row, idx, col_types)
            errors.extend(row_errors[:5])  # cap per row

            if len(errors) >= 500:  # stop collecting after 500 errors
                break

        # Quality score components
        total_cells = total * max(len(headers), 1)
        null_total = sum(null_counts.values())
        completeness = 1.0 - (null_total / max(total_cells, 1))
        validity = 1.0 - (len(errors) / max(total, 1))
        uniqueness = 1.0 - (duplicate_count / max(total, 1))
        # Consistency = no mixed types in numeric cols (approximation)
        consistency = min(completeness, validity)
        quality_score = (completeness * 0.3 + validity * 0.3 + uniqueness * 0.25 + consistency * 0.15)

        # Sample errors for display (max 50)
        error_samples = errors[:50]

        return DatasetValidationResponse(
            valid=len(errors) == 0 and duplicate_count < total * 0.5,
            total_rows=total,
            error_count=len(errors),
            warning_count=duplicate_count,
            columns=column_mappings,
            error_samples=error_samples,
            quality_score=round(quality_score * 100, 2),
            completeness=round(completeness * 100, 2),
            validity=round(validity * 100, 2),
            consistency=round(consistency * 100, 2),
            uniqueness=round(uniqueness * 100, 2),
        )

    async def create_dataset_record(
        self,
        db: AsyncSession,
        *,
        org_id: UUID,
        user_id: UUID,
        name: str,
        source_type: DatasetSourceType,
        file_path: str,
        file_size_bytes: int,
        checksum: str,
        row_count: int | None = None,
        column_count: int | None = None,
    ) -> Any:
        """Create (or return existing) dataset record. Uses checksum for dedup."""
        from ..models.dataset import Dataset
        repo = DatasetRepository(Dataset)

        # Idempotency: same file already uploaded
        existing = await repo.get_by_checksum(db, org_id, checksum)
        if existing and existing.status not in (
            DatasetStatus.FAILED, DatasetStatus.ARCHIVED
        ):
            return existing

        dataset = Dataset(
            organization_id=org_id,
            name=name,
            source_type=source_type,
            status=DatasetStatus.UPLOADED,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            row_count=row_count,
            column_count=column_count,
            imported_by_id=user_id,
        )
        db.add(dataset)
        await db.flush()
        await db.refresh(dataset)
        return dataset

    async def persist_column_schema(
        self,
        db: AsyncSession,
        dataset_id: UUID,
        mappings: list[ColumnMappingInfo],
    ) -> None:
        """Save detected column schema for a dataset."""
        from ..models.dataset import Dataset
        repo = DatasetRepository(Dataset)
        cols = [
            {
                "name": m.source_column,
                "data_type": m.data_type,
                "mapped_to": f"{m.target_entity}.{m.target_field}" if m.target_entity and m.target_field else None,
                "is_nullable": True,
                "sample_values": None,
            }
            for m in mappings
        ]
        await repo.create_column_mapping(db, dataset_id, cols)

    async def create_import_job(
        self,
        db: AsyncSession,
        *,
        org_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        job_type: ImportJobType = ImportJobType.IMPORT,
    ) -> Any:
        """Create an import job record and return it."""
        from ..models.dataset import ImportJob
        job = ImportJob(
            organization_id=org_id,
            dataset_id=dataset_id,
            status=ImportJobStatus.PENDING,
            triggered_by_id=user_id,
            job_type=job_type,
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        return job

    async def run_import(
        self,
        db: AsyncSession,
        *,
        import_job_id: UUID,
        headers: list[str],
        rows: list[list[Any]],
        column_mappings: list[ColumnMappingInfo],
        org_id: UUID,
    ) -> dict[str, Any]:
        """Execute the ETL pipeline for a dataset. Updates import job on completion.

        This is the core transformation logic. It processes rows into the domain
        tables (customers, products, orders, order_line_items).
        """
        from ..models.dataset import Dataset, ImportJob

        job_stmt = __import__("sqlalchemy", fromlist=["select"]).select(ImportJob).where(
            ImportJob.id == import_job_id
        )
        from sqlalchemy import select
        job_result = await db.execute(select(ImportJob).where(ImportJob.id == import_job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValidationError(message="Import job not found.")

        job.status = ImportJobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        job.total_rows = len(rows)
        db.add(job)
        await db.flush()

        col_map = {m.source_column: m for m in column_mappings}
        field_to_col: dict[str, str] = {}
        for m in column_mappings:
            if m.target_entity and m.target_field:
                field_to_col[f"{m.target_entity}.{m.target_field}"] = m.source_column

        def _get(row: list[Any], field: str) -> Any:
            col = field_to_col.get(field)
            if col is None:
                return None
            idx = headers.index(col) if col in headers else -1
            return row[idx] if 0 <= idx < len(row) else None

        def _clean_str(v: Any) -> str | None:
            return str(v).strip() if v is not None and str(v).strip() else None

        def _clean_decimal(v: Any) -> Decimal | None:
            if v is None:
                return None
            try:
                return Decimal(str(v).strip().lstrip("$€£₹").replace(",", ""))
            except InvalidOperation:
                return None

        def _clean_int(v: Any) -> int | None:
            if v is None:
                return None
            try:
                return int(str(v).strip().replace(",", ""))
            except (ValueError, TypeError):
                return None

        def _clean_date(v: Any) -> datetime | None:
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v
            sv = str(v).strip()
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(sv, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            return None

        from ..models.customer import Customer
        from ..models.order import Order, OrderLineItem, OrderSource, OrderStatus, PaymentStatus, PaymentMethod
        from ..models.product import Product, Category
        from sqlalchemy import and_

        valid_rows = 0
        invalid_rows = 0
        error_log: list[dict[str, Any]] = []

        # Cache for lookups within this import session
        customer_cache: dict[str, Any] = {}
        product_cache: dict[str, Any] = {}

        for idx, row in enumerate(rows):
            try:
                # ---- Customer ----
                customer_ext_id = _clean_str(_get(row, "customer.external_id"))
                customer_email = _clean_str(_get(row, "customer.email"))
                customer_key = customer_ext_id or customer_email

                customer = None
                if customer_key and customer_key in customer_cache:
                    customer = customer_cache[customer_key]
                elif customer_key:
                    # Look up existing
                    lookup = select(Customer).where(
                        and_(Customer.organization_id == org_id)
                    )
                    if customer_ext_id:
                        lookup = lookup.where(Customer.external_id == customer_ext_id)
                    elif customer_email:
                        lookup = lookup.where(Customer.email == customer_email)
                    r = await db.execute(lookup)
                    customer = r.scalar_one_or_none()

                if customer is None and (customer_ext_id or customer_email):
                    first = _clean_str(_get(row, "customer.first_name")) or "Unknown"
                    last = _clean_str(_get(row, "customer.last_name")) or ""
                    customer = Customer(
                        organization_id=org_id,
                        external_id=customer_ext_id,
                        email=customer_email,
                        first_name=first,
                        last_name=last,
                    )
                    db.add(customer)
                    await db.flush()
                    await db.refresh(customer)
                    if customer_key:
                        customer_cache[customer_key] = customer

                # ---- Product ----
                product_ext_id = _clean_str(_get(row, "product.external_id"))
                product_name = _clean_str(_get(row, "product.name"))
                product_sku = _clean_str(_get(row, "product.sku"))
                product_key = product_ext_id or product_sku or product_name

                product = None
                if product_key and product_key in product_cache:
                    product = product_cache[product_key]
                elif product_key:
                    lookup = select(Product).where(
                        and_(Product.organization_id == org_id)
                    )
                    if product_ext_id:
                        lookup = lookup.where(Product.external_id == product_ext_id)
                    elif product_sku:
                        lookup = lookup.where(Product.sku == product_sku)
                    r = await db.execute(lookup)
                    product = r.scalar_one_or_none()

                if product is None and product_name:
                    from ..models.product import ProductStatus
                    product = Product(
                        organization_id=org_id,
                        name=product_name,
                        external_id=product_ext_id,
                        sku=product_sku,
                        brand=_clean_str(_get(row, "product.brand")),
                        status=ProductStatus.ACTIVE,
                    )
                    db.add(product)
                    await db.flush()
                    await db.refresh(product)
                    if product_key:
                        product_cache[product_key] = product

                # ---- Order ----
                order_ext_id = _clean_str(_get(row, "order.external_id"))
                order_number = _clean_str(_get(row, "order.order_number"))
                order_date = _clean_date(_get(row, "order.order_date")) or datetime.now(timezone.utc)
                total_amount = _clean_decimal(_get(row, "order.total_amount")) or Decimal("0")
                discount_amount = _clean_decimal(_get(row, "order.discount_amount")) or Decimal("0")
                tax_amount = _clean_decimal(_get(row, "order.tax_amount")) or Decimal("0")
                shipping_amount = _clean_decimal(_get(row, "order.shipping_amount")) or Decimal("0")
                subtotal = total_amount - tax_amount - shipping_amount + discount_amount
                currency = _clean_str(_get(row, "order.currency")) or "USD"

                raw_status = _clean_str(_get(row, "order.status"))
                try:
                    order_status = OrderStatus(raw_status.upper()) if raw_status else OrderStatus.DELIVERED
                except ValueError:
                    order_status = OrderStatus.DELIVERED

                raw_pm = _clean_str(_get(row, "order.payment_method"))
                try:
                    pay_method = PaymentMethod(raw_pm.upper().replace(" ", "_")) if raw_pm else None
                except ValueError:
                    pay_method = PaymentMethod.OTHER

                # Check for existing order (idempotency)
                existing_order = None
                if order_ext_id:
                    from sqlalchemy.exc import NoResultFound
                    chk = select(Order).where(
                        and_(Order.organization_id == org_id, Order.external_id == order_ext_id)
                    )
                    r = await db.execute(chk)
                    existing_order = r.scalar_one_or_none()

                if existing_order is None:
                    order = Order(
                        organization_id=org_id,
                        external_id=order_ext_id,
                        order_number=order_number,
                        customer_id=customer.id if customer else None,
                        order_date=order_date,
                        status=order_status,
                        subtotal=max(subtotal, Decimal("0")),
                        tax_amount=tax_amount,
                        shipping_amount=shipping_amount,
                        discount_amount=discount_amount,
                        total_amount=total_amount,
                        currency=currency[:3].upper() if currency else "USD",
                        payment_status=PaymentStatus.PAID,
                        payment_method=pay_method,
                        source=OrderSource.CSV_IMPORT,
                    )
                    db.add(order)
                    await db.flush()
                    await db.refresh(order)

                    # ---- Order Line Item ----
                    unit_price = _clean_decimal(_get(row, "order_line_item.unit_price")) or total_amount
                    quantity = _clean_int(_get(row, "order_line_item.quantity")) or 1
                    cost_price = _clean_decimal(_get(row, "order_line_item.cost_unit_price"))
                    line_discount = _clean_decimal(_get(row, "order.discount_amount")) or Decimal("0")
                    line_total = unit_price * quantity - line_discount

                    line_item = OrderLineItem(
                        order_id=order.id,
                        organization_id=org_id,
                        product_id=product.id if product else None,
                        product_name_snapshot=product.name if product else "Unknown",
                        sku_snapshot=product_sku,
                        quantity=quantity,
                        unit_price=unit_price,
                        discount_amount=line_discount,
                        tax_amount=tax_amount,
                        line_total=max(line_total, Decimal("0")),
                        cost_unit_price=cost_price,
                    )
                    db.add(line_item)
                    await db.flush()

                valid_rows += 1

            except Exception as exc:
                invalid_rows += 1
                error_log.append({
                    "row": idx + 2,
                    "error": str(exc)[:200],
                })
                logger.warning("Row %d import error: %s", idx + 2, exc)
                if invalid_rows > 1000:
                    error_log.append({"row": -1, "error": "Error limit reached; remaining rows skipped."})
                    break

        # Update job record
        now = datetime.now(timezone.utc)
        job.status = ImportJobStatus.COMPLETED if invalid_rows < len(rows) else ImportJobStatus.FAILED
        job.completed_at = now
        job.valid_rows = valid_rows
        job.invalid_rows = invalid_rows
        job.error_count = len(error_log)
        job.error_log = error_log[:100]
        job.summary = {
            "total_rows": len(rows),
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "completed_at": now.isoformat(),
        }
        db.add(job)

        # Update dataset status
        dataset_result = await db.execute(
            select(Dataset).where(Dataset.id == job.dataset_id)
        )
        dataset = dataset_result.scalar_one_or_none()
        if dataset:
            dataset.status = DatasetStatus.IMPORTED if valid_rows > 0 else DatasetStatus.FAILED
            dataset.row_count = valid_rows
            dataset.last_imported_at = now
            db.add(dataset)

        await db.flush()
        logger.info(
            "Import job completed.",
            extra={
                "import_job_id": str(import_job_id),
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
            },
        )
        return {
            "import_job_id": str(import_job_id),
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "error_count": len(error_log),
        }


ingestion_service = IngestionService()
