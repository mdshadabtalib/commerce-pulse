from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import PermissionRequiredError, TenantIsolationError
from ..core.logging import get_logger

if TYPE_CHECKING:
    from ..models.organization import Permission as PermissionModel
    from ..models.organization import Role, RolePermission
    from ..models.user import User

logger = get_logger(__name__)


@dataclass
class PermissionDef:
    slug: str
    name: str
    category: str
    description: str


class RBACService:
    PERMISSIONS: list[PermissionDef] = [
        PermissionDef("org:read", "Read Organization", "admin", "View organization details"),
        PermissionDef("org:update", "Update Organization", "admin", "Update organization settings"),
        PermissionDef("org:delete", "Delete Organization", "admin", "Delete the organization"),
        PermissionDef("users:invite", "Invite Users", "admin", "Invite new users to the organization"),
        PermissionDef("users:manage", "Manage Users", "admin", "Manage organization members"),
        PermissionDef("roles:manage", "Manage Roles", "admin", "Create and manage custom roles"),
        PermissionDef("billing:manage", "Manage Billing", "admin", "Manage billing and subscriptions"),
        PermissionDef("integrations:manage", "Manage Integrations", "admin", "Configure third-party integrations"),
        PermissionDef("analytics:view", "View Analytics", "analytics", "View analytics dashboards"),
        PermissionDef("dashboards:create", "Create Dashboards", "analytics", "Create custom dashboards"),
        PermissionDef("dashboards:manage", "Manage Dashboards", "analytics", "Manage all dashboards"),
        PermissionDef("data:import", "Import Data", "data", "Import datasets"),
        PermissionDef("data:manage", "Manage Data", "data", "Manage datasets and columns"),
        PermissionDef("data:export", "Export Data", "data", "Export datasets"),
        PermissionDef("reports:view", "View Reports", "reports", "View generated reports"),
        PermissionDef("reports:create", "Create Reports", "reports", "Create custom reports"),
        PermissionDef("reports:manage", "Manage Reports", "reports", "Manage all reports"),
        PermissionDef("reports:scheduled", "Scheduled Reports", "reports", "Configure scheduled report deliveries"),
        PermissionDef("settings:read", "Read Settings", "settings", "View organization settings"),
        PermissionDef("settings:manage", "Manage Settings", "settings", "Update organization settings"),
        PermissionDef("api_keys:create", "Create API Keys", "api", "Create API keys for integrations"),
        PermissionDef("api_keys:manage", "Manage API Keys", "api", "Revoke and manage API keys"),
    ]

    _instance: "RBACService | None" = None

    def __new__(cls) -> "RBACService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_permission_slugs(cls) -> list[str]:
        return [p.slug for p in cls.PERMISSIONS]

    @classmethod
    def get_permissions_by_category(cls) -> dict[str, list[PermissionDef]]:
        result: dict[str, list[PermissionDef]] = {}
        for p in cls.PERMISSIONS:
            result.setdefault(p.category, []).append(p)
        return result

    async def populate_default_permissions(self, db: AsyncSession) -> None:
        from ..models.organization import Permission as PermissionModel, PermissionCategory

        stmt = select(PermissionModel.slug)
        result = await db.execute(stmt)
        existing_slugs = set(result.scalars().all())

        new_permissions = [
            PermissionModel(
                slug=p.slug,
                name=p.name,
                category=PermissionCategory(p.category),
                description=p.description,
            )
            for p in self.PERMISSIONS
            if p.slug not in existing_slugs
        ]
        if new_permissions:
            db.add_all(new_permissions)
            await db.flush()
        logger.info("Default permissions populated (idempotent).", extra={"new_count": len(new_permissions)})

    async def create_default_roles_for_org(self, db: AsyncSession, org_id: UUID) -> None:
        from ..models.organization import Permission as PermissionModel, Role, RolePermission

        perm_stmt = select(PermissionModel)
        perm_result = await db.execute(perm_stmt)
        all_perms: dict[str, UUID] = {p.slug: p.id for p in perm_result.scalars().all()}

        owner_slugs = set(all_perms.keys())
        admin_slugs = {
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
        analyst_slugs = {
            "analytics:view",
            "dashboards:create",
            "data:import", "data:export",
            "reports:view", "reports:create",
        }
        viewer_slugs = {
            "analytics:view",
            "reports:view",
        }

        role_configs = [
            {"name": "Owner", "slug": "owner", "tier": "owner", "perms": owner_slugs},
            {"name": "Admin", "slug": "admin", "tier": "admin", "perms": admin_slugs},
            {"name": "Analyst", "slug": "analyst", "tier": "analyst", "perms": analyst_slugs},
            {"name": "Viewer", "slug": "viewer", "tier": "viewer", "perms": viewer_slugs},
        ]

        for cfg in role_configs:
            existing_stmt = select(Role).where(
                Role.organization_id == org_id,
                Role.slug == cfg["slug"],
                Role.is_system == True,
            )
            existing_result = await db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                continue

            role = Role(
                organization_id=org_id,
                name=cfg["name"],
                slug=cfg["slug"],
                tier=cfg["tier"],
                is_system=True,
                description=f"System role: {cfg['name']}",
            )
            db.add(role)
            await db.flush()

            for slug in cfg["perms"]:
                perm_id = all_perms.get(slug)
                if perm_id:
                    db.add(RolePermission(role_id=role.id, permission_id=perm_id))

        await db.flush()
        logger.info("Default roles created for organization.", extra={"org_id": str(org_id)})

    async def user_has_permission(
        self,
        db: AsyncSession,
        user: "User",
        organization_id: UUID,
        permission_slug: str,
    ) -> bool:
        from ..models.organization import OrganizationMember, Permission as PermissionModel, Role, RolePermission

        member_stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id,
        )
        if hasattr(OrganizationMember, "status"):
            member_stmt = member_stmt.where(
                OrganizationMember.status.in_(["ACTIVE", "ACCEPTED"])
            )
        member_result = await db.execute(member_stmt)
        member = member_result.scalar_one_or_none()
        if not member:
            return False

        if str(member.organization_id) != str(organization_id):
            raise TenantIsolationError(
                details={
                    "user_org": str(member.organization_id),
                    "requested_org": str(organization_id),
                }
            )

        role_id = getattr(member, "role_id", None)
        if not role_id:
            return False

        role_stmt = select(Role).where(Role.id == role_id)
        role_result = await db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if role and getattr(role, "tier", None) and role.tier.lower() == "owner":
            return True

        perm_stmt = (
            select(PermissionModel)
            .join(RolePermission, RolePermission.permission_id == PermissionModel.id)
            .where(
                RolePermission.role_id == role_id,
                PermissionModel.slug == permission_slug,
            )
        )
        perm_result = await db.execute(perm_stmt)
        return perm_result.scalar_one_or_none() is not None

    async def require_permission(
        self,
        db: AsyncSession,
        user: "User",
        organization_id: UUID,
        permission_slug: str,
    ) -> None:
        has = await self.user_has_permission(db, user, organization_id, permission_slug)
        if not has:
            raise PermissionRequiredError(required_permissions=[permission_slug])

    def require_permission_dep(
        self,
        permission_slug: str,
    ) -> Callable[..., None]:
        async def dependency(
            db: AsyncSession,
            user: "User",
            organization_id: UUID | None = None,
        ) -> None:
            if organization_id is None:
                from ..core.deps import org_id_var
                organization_id = org_id_var.get()
            if organization_id is None:
                raise PermissionRequiredError(required_permissions=[permission_slug])
            await self.require_permission(db, user, UUID(str(organization_id)), permission_slug)
        return dependency
