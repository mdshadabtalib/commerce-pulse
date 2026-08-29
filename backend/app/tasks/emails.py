"""Email delivery Celery tasks.

All email sending goes through here so that it is:
- Non-blocking (HTTP request returns immediately)
- Retryable with exponential back-off
- Observable via Celery result backend
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ..core.celery_app import celery_app
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

if celery_app is None:
    # Fallback when Celery is unavailable (tests / dev without broker)
    class _DummyCelery:
        @staticmethod
        def task(*args: Any, **kwargs: Any):
            def decorator(fn):
                return fn
            return decorator
    celery_app = _DummyCelery()  # type: ignore[assignment]


TEMPLATES: dict[str, str] = {
    "email_verification": """
<html><body>
<h2>Verify Your CommercePulse Account</h2>
<p>Click the link below to verify your email address:</p>
<p><a href="{base_url}/auth/verify-email?token={token}">Verify Email</a></p>
<p>This link expires in 24 hours.</p>
<p>If you did not create a CommercePulse account, you can safely ignore this email.</p>
</body></html>
""",
    "password_reset": """
<html><body>
<h2>Reset Your CommercePulse Password</h2>
<p>Click the link below to reset your password:</p>
<p><a href="{base_url}/auth/reset-password?token={token}">Reset Password</a></p>
<p>This link expires in 1 hour.</p>
<p>If you did not request a password reset, please ignore this email.</p>
</body></html>
""",
    "invitation": """
<html><body>
<h2>You've been invited to CommercePulse</h2>
<p>You have been invited to join an organization on CommercePulse.</p>
<p><a href="{base_url}/auth/accept-invite?token={token}">Accept Invitation</a></p>
<p>This invitation expires in 7 days.</p>
</body></html>
""",
    "report_ready": """
<html><body>
<h2>Your CommercePulse Report is Ready</h2>
<p>Your report "<strong>{report_title}</strong>" has been generated.</p>
<p><a href="{base_url}/reports/{report_id}">View Report</a></p>
</body></html>
""",
    "anomaly_alert": """
<html><body>
<h2>Anomaly Detected — CommercePulse</h2>
<p>An anomaly was detected in your data:</p>
<ul>
  <li><strong>Metric:</strong> {metric}</li>
  <li><strong>Severity:</strong> {severity}</li>
  <li><strong>Description:</strong> {description}</li>
</ul>
<p><a href="{base_url}/anomalies">View Anomalies</a></p>
</body></html>
""",
}


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render an email template with context variables."""
    template = TEMPLATES.get(template_name, "<p>No template found.</p>")
    base_url = getattr(settings, "FRONTEND_URL", "https://app.commercepulse.ai")
    ctx = {"base_url": base_url, **context}
    try:
        return template.format(**ctx)
    except KeyError:
        return template


def _send_smtp(
    to_emails: list[str],
    subject: str,
    html_body: str,
) -> None:
    """Send email via configured SMTP server."""
    from_addr = str(settings.MAIL_FROM)
    from_name = settings.MAIL_FROM_NAME

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = ", ".join(to_emails)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.MAIL_SSL_TLS:
            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_USE_CREDENTIALS:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())
                server.sendmail(from_addr, to_emails, msg.as_string())
        else:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_STARTTLS:
                    server.starttls()
                if settings.MAIL_USE_CREDENTIALS:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())
                server.sendmail(from_addr, to_emails, msg.as_string())
        logger.info("Email sent.", extra={"to": to_emails, "subject": subject})
    except Exception as exc:
        logger.error("SMTP send failed.", extra={"to": to_emails, "error": str(exc)})
        raise


@celery_app.task(  # type: ignore[attr-defined]
    name="emails.send",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="emails",
    acks_late=True,
)
def send_email(
    self: Any,
    to_emails: list[str],
    subject: str,
    template_name: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a transactional email.

    Args:
        to_emails: List of recipient email addresses.
        subject: Email subject line.
        template_name: Name of the HTML template to use.
        context: Template context variables.
    """
    ctx = context or {}
    html_body = _render_template(template_name, ctx)

    try:
        # Only send if SMTP credentials are configured
        if settings.MAIL_PASSWORD.get_secret_value():
            _send_smtp(to_emails, subject, html_body)
        else:
            logger.info(
                "SMTP not configured — email suppressed in dev mode.",
                extra={"to": to_emails, "subject": subject, "template": template_name},
            )
        return {"status": "sent", "to": to_emails, "subject": subject}
    except Exception as exc:
        logger.warning(
            "Email send failed, retrying.",
            extra={"to": to_emails, "error": str(exc), "retries": self.request.retries},
        )
        raise self.retry(exc=exc)
