from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger

if TYPE_CHECKING:
    from ..models.analytics import Notification

logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationService:
    async def create_in_app(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        org_id: UUID | None = None,
        type: str,
        title: str,
        body: str | None = None,
        action_url: str | None = None,
        action_text: str | None = None,
        data: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> "Notification":
        """Create an in-app notification for a user."""
        from ..models.analytics import Notification, NotificationChannel, NotificationStatus

        notif = Notification(
            user_id=user_id,
            organization_id=org_id,
            type=type,
            title=title,
            body=body,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.PENDING,
            action_url=action_url,
            action_text=action_text,
            data=data or {},
            priority=priority,
        )
        db.add(notif)
        await db.flush()
        await db.refresh(notif)
        logger.debug(
            "Created in-app notification.",
            extra={"user_id": str(user_id), "type": type},
        )
        return notif

    async def mark_read(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_id: UUID,
    ) -> bool:
        """Mark a single notification as read. Returns True if updated."""
        from ..models.analytics import Notification, NotificationStatus

        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        notif = result.scalar_one_or_none()
        if notif and notif.status != NotificationStatus.READ:
            notif.status = NotificationStatus.READ
            notif.read_at = _utcnow()
            db.add(notif)
            await db.flush()
            return True
        return False

    async def mark_all_read(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Mark all unread notifications for a user as read. Returns count updated."""
        from ..models.analytics import Notification, NotificationStatus

        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.status != NotificationStatus.READ,
            )
        )
        result = await db.execute(stmt)
        unread = list(result.scalars().all())
        now = _utcnow()
        for n in unread:
            n.status = NotificationStatus.READ
            n.read_at = now
            db.add(n)
        if unread:
            await db.flush()
        return len(unread)

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list["Notification"]:
        """List notifications for a user, most recent first."""
        from ..models.analytics import Notification, NotificationStatus

        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.status != NotificationStatus.READ)
        stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Count unread notifications for a user."""
        from sqlalchemy import func
        from ..models.analytics import Notification, NotificationStatus

        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.status != NotificationStatus.READ,
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one() or 0


notification_service = NotificationService()
