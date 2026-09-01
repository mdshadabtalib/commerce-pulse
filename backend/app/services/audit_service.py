from __future__ import annotations

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger

if TYPE_CHECKING:
    from ..models.analytics import AuditLog
    from ..models.user import User
    from ..models.organization import Organization

logger = get_logger(__name__)


class AuditService:
    async def log(
        self,
        db: AsyncSession,
        action: str,
        *,
        user: "User | None" = None,
        organization: "Organization | UUID | None" = None,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a security-sensitive audit event.
        Errors are swallowed so that a logging failure never breaks the request.
        """
        try:
            from ..models.analytics import AuditLog

            user_id = (
                getattr(user, "id", None)
                if user and not isinstance(user, UUID)
                else (user if isinstance(user, UUID) else None)
            )
            org_id: UUID | None = None
            if organization is not None:
                org_id = (
                    getattr(organization, "id", None)
                    if not isinstance(organization, UUID)
                    else organization
                )
            elif user is not None and hasattr(user, "organization_memberships"):
                try:
                    memberships = getattr(user, "organization_memberships", []) or []
                    if memberships:
                        org_id = getattr(memberships[0], "organization_id", None)
                except Exception:
                    pass

            entry = AuditLog(
                action=action,
                user_id=user_id,
                organization_id=org_id,
                resource_type=resource_type or "unknown",
                resource_id=resource_id if isinstance(resource_id, UUID) else (
                    UUID(str(resource_id)) if resource_id else None
                ),
                ip_address=ip_address,
                user_agent=user_agent[:512] if user_agent else None,
                metadata_=metadata,
            )
            db.add(entry)
            await db.flush()
        except Exception as exc:
            logger.warning(
                "Failed to write audit log. Swallowing to preserve request flow.",
                extra={
                    "action": action,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )


audit_service = AuditService()
