from __future__ import annotations

import re
import unicodedata
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..core.logging import get_logger
from .base import BaseRepository

if TYPE_CHECKING:
    from ..models.organization import (
        Organization,
        OrganizationMember,
        Permission,
        Role,
        RolePermission,
    )
    from ..models.user import User

logger = get_logger(__name__)


class OrganizationRepository(BaseRepository):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> "Organization | None":
        stmt = select(self.model).where(self.model.slug == slug)
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_user(self, db: AsyncSession, user_id: UUID) -> list["Organization"]:
        from ..models.organization import OrganizationMember

        stmt = (
            select(self.model)
            .join(OrganizationMember, OrganizationMember.organization_id == self.model.id)
            .where(OrganizationMember.user_id == user_id)
        )
        if hasattr(OrganizationMember, "status"):
            stmt = stmt.where(OrganizationMember.status == "ACTIVE")
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        stmt = stmt.options(selectinload(self.model.members))
        result = await db.execute(stmt)
        return list(result.scalars().unique().all())

    async def create_with_owner(
        self,
        db: AsyncSession,
        org_data_dict: dict,
        user_id: UUID,
    ) -> "Organization":
        from ..db.base import utc_now
        from ..models.organization import OrganizationMember, Role
        from ..services.rbac_service import RBACService

        org_data = dict(org_data_dict)

        if "slug" not in org_data or not org_data["slug"]:
            org_data["slug"] = await self.generate_slug(db, org_data.get("name", ""))

        org_data["created_by_id"] = user_id

        org = self.model(**org_data)
        db.add(org)
        await db.flush()

        await RBACService().create_default_roles_for_org(db, org.id)

        owner_role_stmt = select(Role).where(
            Role.organization_id == org.id,
            Role.slug == "owner",
        )
        owner_role_result = await db.execute(owner_role_stmt)
        owner_role: Optional[Role] = owner_role_result.scalar_one_or_none()

        owner_member = OrganizationMember(
            organization_id=org.id,
            user_id=user_id,
            role_id=owner_role.id if owner_role else None,
            is_owner=True,
            status="ACTIVE",
            joined_at=utc_now(),
        )
        db.add(owner_member)
        await db.flush()

        logger.info(
            "Created organization with owner.",
            extra={"organization_id": str(org.id), "owner_id": str(user_id)},
        )
        return org

    async def _create_default_roles(self, db: AsyncSession, organization_id: UUID) -> None:
        from ..models.organization import (
            Permission,
            Role,
            RolePermission,
        )

        perm_stmt = select(Permission)
        perm_result = await db.execute(perm_stmt)
        all_permissions = list(perm_result.scalars().all())
        perm_by_slug = {p.slug: p for p in all_permissions}

        default_role_configs = [
            {
                "name": "Owner",
                "slug": "owner",
                "tier": "owner",
                "is_system": True,
                "description": "Full access to the organization",
            },
            {
                "name": "Admin",
                "slug": "admin",
                "tier": "admin",
                "is_system": True,
                "description": "Administrative access to most features",
            },
            {
                "name": "Analyst",
                "slug": "analyst",
                "tier": "analyst",
                "is_system": True,
                "description": "Data analysis and reporting access",
            },
            {
                "name": "Viewer",
                "slug": "viewer",
                "tier": "viewer",
                "is_system": True,
                "description": "Read-only access to analytics and reports",
            },
        ]

        owner_permissions = set(perm_by_slug.keys())
        admin_permissions = {
            "org:read", "org:update",
            "users:invite", "users:manage",
            "roles:manage",
            "integrations:manage",
            "analytics:view",
            "dashboards:create", "dashboards:manage",
            "data:import", "data:manage", "data:export",
            "reports:view", "reports:create", "reports:manage", "reports:scheduled",
            "settings:read", "settings:manage",
            "api_keys:create", "api_keys:manage",
        }
        analyst_permissions = {
            "analytics:view",
            "dashboards:create",
            "data:import", "data:export",
            "reports:view", "reports:create",
        }
        viewer_permissions = {
            "analytics:view",
            "reports:view",
        }

        role_perm_sets = [
            owner_permissions,
            admin_permissions,
            analyst_permissions,
            viewer_permissions,
        ]

        for config, perm_slugs in zip(default_role_configs, role_perm_sets):
            role = Role(
                organization_id=organization_id,
                name=config["name"],
                slug=config["slug"],
                tier=config["tier"],
                is_system=config["is_system"],
                description=config["description"],
            )
            db.add(role)
            await db.flush()

            for slug in perm_slugs:
                perm = perm_by_slug.get(slug)
                if perm:
                    rp = RolePermission(role_id=role.id, permission_id=perm.id)
                    db.add(rp)

    async def invite_member(
        self,
        db: AsyncSession,
        org_id: UUID,
        email: str,
        role_id: UUID,
        invited_by_id: UUID,
    ) -> "OrganizationMember":
        from ..models.organization import OrganizationMember, OrganizationMemberStatus

        member = OrganizationMember(
            organization_id=org_id,
            user_id=None,
            role_id=role_id,
            status=OrganizationMemberStatus.INVITED,
            invited_by_id=invited_by_id,
            invite_accepted_at=None,
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)

        try:
            from ..core.celery_app import celery_app
            if celery_app:
                celery_app.send_task(
                    "emails.send",
                    args=[[email], "Organization Invitation", "invitation", {"org_id": str(org_id)}],
                    queue="emails",
                )
        except Exception as exc:
            logger.warning(
                "Failed to queue invite email, continuing.",
                extra={"org_id": str(org_id), "email": email, "error": str(exc)},
            )

        logger.info(
            "Invited member to organization.",
            extra={"org_id": str(org_id), "email": email, "invited_by": str(invited_by_id)},
        )
        return member

    async def get_member_by_user_id(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> "OrganizationMember | None":
        from ..models.organization import OrganizationMember

        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if hasattr(OrganizationMember, "status"):
            stmt = stmt.where(OrganizationMember.status.in_(["ACTIVE", "ACCEPTED"]))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_member(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        removed_by_id: UUID,
    ) -> None:
        from ..models.organization import OrganizationMember, OrganizationMemberStatus

        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        if member:
            member.status = OrganizationMemberStatus.REMOVED
            db.add(member)
            await db.flush()
            logger.info(
                "Removed member from organization.",
                extra={"org_id": str(org_id), "user_id": str(user_id), "removed_by": str(removed_by_id)},
            )

    async def change_member_role(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        new_role_id: UUID,
        changed_by_id: UUID,
    ) -> None:
        from ..models.organization import OrganizationMember

        member = await self.get_member_by_user_id(db, org_id, user_id)
        if member:
            member.role_id = new_role_id
            if hasattr(member, "role_updated_by_id"):
                member.role_updated_by_id = changed_by_id
                member.role_updated_at = func.now()
            db.add(member)
            await db.flush()
            logger.info(
                "Changed member role.",
                extra={
                    "org_id": str(org_id),
                    "user_id": str(user_id),
                    "new_role_id": str(new_role_id),
                    "changed_by": str(changed_by_id),
                },
            )

    async def get_roles(self, db: AsyncSession, org_id: UUID) -> list["Role"]:
        from ..models.organization import Role

        stmt = select(Role).where(Role.organization_id == org_id).order_by(Role.tier, Role.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_permission_ids_for_role(self, db: AsyncSession, role_id: UUID) -> set[UUID]:
        from ..models.organization import RolePermission

        stmt = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        result = await db.execute(stmt)
        return {row[0] for row in result.all()}

    async def user_has_permission(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        permission_slug: str,
    ) -> bool:
        from ..models.organization import OrganizationMember, Permission, Role, RolePermission

        member_stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if hasattr(OrganizationMember, "status"):
            member_stmt = member_stmt.where(OrganizationMember.status.in_(["ACTIVE", "ACCEPTED"]))
        member_result = await db.execute(member_stmt)
        member = member_result.scalar_one_or_none()
        if not member:
            return False

        role_id = getattr(member, "role_id", None)
        role_tier = None
        if role_id:
            role_stmt = select(Role).where(Role.id == role_id)
            role_result = await db.execute(role_stmt)
            role = role_result.scalar_one_or_none()
            if role:
                role_tier = getattr(role, "tier", None)
                if role_tier and role_tier.lower() == "owner":
                    return True

        if not role_id:
            return False

        perm_stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.slug == permission_slug,
                )
            )
        )
        perm_result = await db.execute(perm_stmt)
        return perm_result.scalar_one_or_none() is not None

    async def generate_slug(self, db: AsyncSession, name: str) -> str:
        base_slug = self._slugify(name)
        if not base_slug:
            base_slug = "org"
        counter = 1
        slug = base_slug
        while await self.exists(db, slug=slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @staticmethod
    def _slugify(value: str) -> str:
        value = str(value)
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^\w\s-]", "", value.lower())
        value = re.sub(r"[-\s]+", "-", value).strip("-_")
        return value[:63]
