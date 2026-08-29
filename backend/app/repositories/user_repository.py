from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..core.security import password_security
from .base import BaseRepository

if TYPE_CHECKING:
    from ..models.user import User
    from ..models.organization import Organization, OrganizationMember

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    async def get_by_email(self, db: AsyncSession, email: str) -> "User | None":
        stmt = select(self.model).where(func.lower(self.model.email) == func.lower(email))
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, db: AsyncSession, ids: list[UUID]) -> list["User"]:
        if not ids:
            return []
        stmt = select(self.model).where(self.model.id.in_(ids))
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_with_memberships(
        self,
        db: AsyncSession,
        user_id: UUID,
        organization_id: UUID | None = None,
    ) -> "User | None":
        from ..models.organization import OrganizationMember

        stmt = select(self.model).where(self.model.id == user_id)
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and organization_id:
            member_stmt = select(OrganizationMember).where(
                and_(
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.organization_id == organization_id,
                )
            )
            member_result = await db.execute(member_stmt)
            _ = member_result.scalar_one_or_none()
        return user

    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> "User | None":
        user = await self.get_by_email(db, email)
        if not user:
            return None
        verified, new_hash = password_security.verify(password, user.hashed_password)
        if not verified:
            return None
        if new_hash:
            user.hashed_password = new_hash
            db.add(user)
            await db.flush()
            logger.info("Password hash migrated for user.", extra={"user_id": str(user.id)})
        return user

    async def update_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        new_password_hash: str,
    ) -> None:
        stmt = select(self.model).where(self.model.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = new_password_hash
            if hasattr(user, "password_updated_at"):
                user.password_updated_at = datetime.utcnow()
            db.add(user)
            await db.flush()
            logger.info("Password updated for user.", extra={"user_id": str(user_id)})

    async def verify_email(self, db: AsyncSession, user_id: UUID) -> None:
        from ..models.user import UserStatus

        stmt = select(self.model).where(self.model.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            from datetime import timezone
            user.email_verified_at = datetime.now(timezone.utc)
            if getattr(user, "status", None) == UserStatus.PENDING_VERIFICATION:
                user.status = UserStatus.ACTIVE
            db.add(user)
            await db.flush()
            logger.info("Email verified for user.", extra={"user_id": str(user_id)})

    async def record_login(
        self,
        db: AsyncSession,
        user_id: UUID,
        ip_address: str | None = None,
    ) -> None:
        stmt = select(self.model).where(self.model.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.last_login_at = datetime.utcnow()
            if ip_address and hasattr(user, "last_login_ip"):
                user.last_login_ip = ip_address
            if hasattr(user, "login_count"):
                user.login_count = (user.login_count or 0) + 1
            db.add(user)
            await db.flush()
