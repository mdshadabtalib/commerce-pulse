"""Report generation Celery tasks."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from ..core.celery_app import celery_app
from ..core.logging import get_logger

logger = get_logger(__name__)

if celery_app is None:
    class _DummyCelery:
        @staticmethod
        def task(*args: Any, **kwargs: Any):
            def decorator(fn):
                return fn
            return decorator
    celery_app = _DummyCelery()  # type: ignore[assignment]


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


@celery_app.task(  # type: ignore[attr-defined]
    name="reports.generate",
    bind=True,
    max_retries=1,
    queue="reports",
    acks_late=True,
    time_limit=600,
    soft_time_limit=550,
)
def generate_report(
    self: Any,
    report_id: str,
    org_id: str,
    report_type: str,
    format: str,
    date_range: dict[str, str],
    filters: dict[str, Any] | None = None,
    sections: list[str] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate a report and store it in object storage.

    Updates the Report record's status and file_url on completion.
    Sends an email notification to the requesting user.

    Args:
        report_id: UUID of the Report record.
        org_id: UUID of the organization.
        report_type: ReportType value.
        format: ReportFormat value (PDF/CSV/EXCEL).
        date_range: dict with start_date and end_date keys.
        filters: Optional analytics filters.
        sections: Optional list of report sections to include.
        user_id: UUID of the requesting user (for notification).
    """
    async def _run() -> dict[str, Any]:
        from ..db.session import async_session_factory
        from ..services.analytics_service import AnalyticsService
        from ..schemas.common import DateRangeFilter
        from ..models.analytics import Report
        from sqlalchemy import select
        from datetime import datetime, timezone, date

        analytics_svc = AnalyticsService()

        start = date.fromisoformat(date_range.get("start_date", str(date.today())))
        end = date.fromisoformat(date_range.get("end_date", str(date.today())))
        dr = DateRangeFilter(start_date=start, end_date=end)

        async with async_session_factory() as db:
            # Mark report as generating
            r = await db.execute(select(Report).where(Report.id == UUID(report_id)))
            report = r.scalar_one_or_none()
            if not report:
                raise ValueError(f"Report {report_id} not found.")
            report.status = "GENERATING"
            report.started_at = datetime.now(timezone.utc)
            db.add(report)
            await db.commit()

            try:
                # Gather analytics data
                kpis = await analytics_svc.get_sales_kpis(db, UUID(org_id), date_range=dr)
                trend = await analytics_svc.get_sales_trend(db, UUID(org_id), date_range=dr, granularity="monthly")

                report_data = {
                    "report_id": report_id,
                    "org_id": org_id,
                    "report_type": report_type,
                    "date_range": date_range,
                    "kpis": kpis.model_dump() if kpis else {},
                    "trend": [p.model_dump() for p in trend] if trend else [],
                }

                # Generate output file
                file_content, content_type, file_ext = await _render_report(
                    format, report_data, report_type, dr
                )
                file_url = await _upload_report(
                    file_content,
                    f"reports/{org_id}/{report_id}.{file_ext}",
                    content_type,
                )

                # Update report record
                now = datetime.now(timezone.utc)
                report.status = "COMPLETED"
                report.completed_at = now
                report.file_url = file_url
                report.file_size_bytes = len(file_content)
                report.summary = report_data.get("kpis", {})
                db.add(report)
                await db.commit()

                # Send notification email if user_id provided
                if user_id:
                    try:
                        from ..core.celery_app import celery_app as app
                        if app:
                            app.send_task(
                                "emails.send",
                                args=[[user_id], "Your Report is Ready", "report_ready", {
                                    "report_title": report.title,
                                    "report_id": report_id,
                                }],
                                queue="emails",
                            )
                    except Exception:
                        pass

                return {"report_id": report_id, "status": "completed", "file_url": file_url}

            except Exception as exc:
                report.status = "FAILED"
                report.error_message = str(exc)[:500]
                db.add(report)
                await db.commit()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("Report generation failed.", extra={"report_id": report_id, "error": str(exc)})
        raise self.retry(exc=exc)


async def _render_report(
    format: str,
    data: dict[str, Any],
    report_type: str,
    date_range: Any,
) -> tuple[bytes, str, str]:
    """Render report data into the requested format. Returns (bytes, content_type, extension)."""
    fmt = format.upper()

    if fmt == "JSON":
        import json
        content = json.dumps(data, default=str, indent=2).encode("utf-8")
        return content, "application/json", "json"

    elif fmt == "CSV":
        import csv, io
        out = io.StringIO()
        kpis = data.get("kpis", {})
        writer = csv.writer(out)
        writer.writerow(["Metric", "Value"])
        for k, v in kpis.items():
            writer.writerow([k, v])
        return out.getvalue().encode("utf-8"), "text/csv", "csv"

    elif fmt in ("PDF", "EXCEL"):
        # For now, fall back to JSON if PDF/Excel libs not installed
        try:
            if fmt == "EXCEL":
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = report_type
                kpis = data.get("kpis", {})
                ws.append(["Metric", "Value"])
                for k, v in kpis.items():
                    ws.append([k, str(v)])
                import io
                buf = io.BytesIO()
                wb.save(buf)
                return buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
        except ImportError:
            pass

        # PDF placeholder using reportlab if available
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as pdf_canvas
            import io
            buf = io.BytesIO()
            c = pdf_canvas.Canvas(buf, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, 750, f"CommercePulse — {report_type}")
            c.setFont("Helvetica", 11)
            y = 720
            kpis = data.get("kpis", {})
            for k, v in kpis.items():
                c.drawString(72, y, f"{k}: {v}")
                y -= 18
                if y < 72:
                    c.showPage()
                    y = 720
            c.save()
            return buf.getvalue(), "application/pdf", "pdf"
        except ImportError:
            pass

        # Ultimate fallback: JSON
        import json
        content = json.dumps(data, default=str, indent=2).encode("utf-8")
        return content, "application/json", "json"

    import json
    content = json.dumps(data, default=str, indent=2).encode("utf-8")
    return content, "application/json", "json"


async def _upload_report(
    content: bytes,
    key: str,
    content_type: str,
) -> str:
    """Upload report to S3 or local tmp. Returns download URL."""
    import os
    from ..core.config import settings

    # Try S3 upload
    if settings.S3_ACCESS_KEY.get_secret_value():
        try:
            import aioboto3
            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT if settings.S3_ENDPOINT != "https://s3.amazonaws.com" else None,
                aws_access_key_id=settings.S3_ACCESS_KEY.get_secret_value(),
                aws_secret_access_key=settings.S3_SECRET_KEY.get_secret_value(),
                region_name=settings.S3_REGION,
            ) as s3:
                await s3.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
            return f"s3://{settings.S3_BUCKET}/{key}"
        except Exception as exc:
            logger.warning("S3 upload failed, falling back to local: %s", exc)

    # Fallback: local tmp
    import tempfile
    tmp_dir = os.path.join(tempfile.gettempdir(), "commercepulse_reports")
    os.makedirs(tmp_dir, exist_ok=True)
    fname = key.replace("/", "_")
    fpath = os.path.join(tmp_dir, fname)
    with open(fpath, "wb") as f:
        f.write(content)
    return f"file://{fpath}"
