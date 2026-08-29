"""Organizations router — multi-tenant org management, members, roles, permissions."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..core.deps import (
    get_current_active_user,
    get_db,
    require_permissions,
    UserLike,
)
from ..core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from ..core.logging import get_logger
from ..repositories.organization_repository import OrganizationRepository
from ..schemas.organization import (
    MemberInvite,
    MemberInviteBatch,
    MemberUpdate,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from ..schemas.user import UserResponse
from ..services.audit_service import audit_service
from ..services.rbac_service import RBACService

logger = get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _org_repo(db: AsyncSession | None = None) -> OrganizationRepository:
    from ..models.organization import Organization
    return OrganizationRepository(Organization)


def _org_response(org: Any) -> OrganizationResponse:
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        status=org.status,
        size=getattr(org, "size", None),
        logo_url=getattr(org, "logo_url", None),
        website=getattr(org, "website", None),
        timezone=org.timezone,
        default_currency=org.default_currency,
        billing_email=getattr(org, "billing_email", None),
        settings=getattr(org, "settings", None),
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


def _member_response(member: Any) -> OrganizationMemberResponse:
    user = member.user
    role = member.role
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=getattr(user, "full_name", None),
        avatar_url=getattr(user, "avatar_url", None),
        phone=getattr(user, "phone", None),
        status=user.status,
        email_verified_at=getattr(user, "email_verified_at", None),
        last_login_at=getattr(user, "last_login_at", None),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    role_resp = None
    if role:
        perms = []
        for rp in getattr(role, "role_permissions", []):
            p = getattr(rp, "permission", None)
            if p:
                perms.append(PermissionResponse(
                    id=p.id, name=p.name, slug=p.slug,
                    description=getattr(p, "description", None),
                    category=getattr(p, "category", ""),
                ))
        role_resp = RoleResponse(
            id=role.id,
            organization_id=role.organization_id,
            name=role.name,
            slug=role.slug,
            description=getattr(role, "description", None),
            is_system=getattr(role, "is_system", False),
            tier=getattr(role, "tier", None),
            permissions=perms,
        )
    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user=user_resp,
        role=role_resp,
        is_owner=getattr(member, "is_owner", False),
        status=member.status,
        joined_at=getattr(member, "joined_at", None),
        last_accessed_at=getattr(member, "last_accessed_at", None),
    )


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
    description="Creates a new organization and assigns the authenticated user as its owner.",
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> OrganizationResponse:
    repo = _org_repo()
    data = payload.model_dump(exclude_none=True)
    org = await repo.create_with_owner(db, data, current_user.id)
    await audit_service.log(db, "org.create", organization=org, resource_type="organization", resource_id=org.id)
    return _org_response(org)


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List organizations for current user",
    description="Returns all organizations the authenticated user is an active member of.",
)
async def list_my_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> list[OrganizationResponse]:
    repo = _org_repo()
    orgs = await repo.get_for_user(db, current_user.id)
    return [_org_response(o) for o in orgs]


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization by ID",
    description="Returns organization details. The authenticated user must be a member.",
)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> OrganizationResponse:
    _assert_org_member(current_user, org_id)
    repo = _org_repo()
    org = await repo.get_or_404(db, org_id)
    return _org_response(org)


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization settings",
    description="Updates the organization. Requires `settings:manage` permission.",
)
async def update_organization(
    org_id: UUID,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("settings:manage")),
) -> OrganizationResponse:
    _assert_org_member(current_user, org_id)
    repo = _org_repo()
    org = await repo.get_or_404(db, org_id)
    updated = await repo.update(db, org, payload)
    await audit_service.log(db, "org.update", organization=org, resource_type="organization", resource_id=org_id)
    return _org_response(updated)


@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization (owner only)",
    description=(
        "Soft-deletes the organization. The caller must be the organization owner. "
        "This is irreversible without manual database intervention."
    ),
)
async def delete_organization(
    org_id: UUID,
    confirm_name: str = Body(..., embed=True, description="Organization name to confirm deletion"),
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("org:delete")),
) -> None:
    _assert_org_member(current_user, org_id)
    _assert_is_owner(current_user)
    repo = _org_repo()
    org = await repo.get_or_404(db, org_id)
    if org.name != confirm_name:
        raise ValidationError(
            message="Organization name confirmation does not match.",
            details={"hint": "Pass the exact organization name in `confirm_name`."},
        )
    await repo.delete(db, org_id, hard=False)
    await audit_service.log(db, "org.delete", organization=org, resource_type="organization", resource_id=org_id)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/members",
    response_model=list[OrganizationMemberResponse],
    summary="List organization members",
    description="Returns all active members of the organization.",
)
async def list_members(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> list[OrganizationMemberResponse]:
    _assert_org_member(current_user, org_id)
    from ..models.organization import OrganizationMember, OrganizationMemberStatus, Role, RolePermission, Permission
    from ..models.user import User
    stmt = (
        select(OrganizationMember)
        .where(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.status == OrganizationMemberStatus.ACTIVE,
            )
        )
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role).options(
                selectinload(Role.role_permissions).joinedload(RolePermission.permission)
            ),
        )
    )
    result = await db.execute(stmt)
    members = list(result.scalars().unique().all())
    return [_member_response(m) for m in members]


@router.post(
    "/{org_id}/members/invite",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a member to the organization",
    description="Sends an invitation email to the specified address. Requires `users:invite` permission.",
)
async def invite_member(
    org_id: UUID,
    payload: MemberInvite,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("users:invite")),
) -> dict:
    _assert_org_member(current_user, org_id)
    repo = _org_repo()

    # Resolve role_id from slug if needed
    role_id: UUID | None = payload.role_id
    if role_id is None and payload.role_slug:
        from ..models.organization import Role
        from sqlalchemy import select
        stmt = select(Role).where(
            and_(Role.organization_id == org_id, Role.slug == payload.role_slug)
        )
        role_result = await db.execute(stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundError(message=f"Role '{payload.role_slug}' not found in this organization.")
        role_id = role.id

    if role_id is None:
        # Default to viewer role
        from ..models.organization import Role
        stmt = select(Role).where(and_(Role.organization_id == org_id, Role.slug == "viewer"))
        role_result = await db.execute(stmt)
        viewer_role = role_result.scalar_one_or_none()
        role_id = viewer_role.id if viewer_role else None

    member = await repo.invite_member(db, org_id, payload.email, role_id, current_user.id)
    await audit_service.log(
        db, "org.member.invite",
        organization=org_id, resource_type="organization_member", resource_id=member.id,
        metadata={"email": payload.email},
    )
    return {"message": f"Invitation sent to {payload.email}."}


@router.post(
    "/{org_id}/members/invite-batch",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Invite multiple members at once",
    description="Batch invite up to 20 members. Requires `users:invite` permission.",
)
async def invite_members_batch(
    org_id: UUID,
    payload: MemberInviteBatch,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("users:invite")),
) -> dict:
    _assert_org_member(current_user, org_id)
    if len(payload.invites) > 20:
        raise ValidationError(message="Cannot invite more than 20 members at once.")
    success, failed = [], []
    repo = _org_repo()
    for invite in payload.invites:
        try:
            role_id = invite.role_id
            if role_id is None and invite.role_slug:
                from ..models.organization import Role
                stmt = select(Role).where(and_(Role.organization_id == org_id, Role.slug == invite.role_slug))
                r = await db.execute(stmt)
                role = r.scalar_one_or_none()
                role_id = role.id if role else None
            await repo.invite_member(db, org_id, invite.email, role_id, current_user.id)
            success.append(invite.email)
        except Exception as e:
            failed.append({"email": invite.email, "error": str(e)})
    return {"invited": success, "failed": failed}


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the organization",
    description="Removes a member. Requires `users:manage` permission. Owners cannot be removed.",
)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("users:manage")),
) -> None:
    _assert_org_member(current_user, org_id)
    if str(user_id) == str(current_user.id):
        raise ValidationError(message="You cannot remove yourself from the organization.")
    repo = _org_repo()
    # Protect owner from removal
    from ..models.organization import OrganizationMember
    stmt = select(OrganizationMember).where(
        and_(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if target and target.is_owner:
        raise AuthorizationError(message="Organization owner cannot be removed. Transfer ownership first.")
    await repo.remove_member(db, org_id, user_id, current_user.id)
    await audit_service.log(
        db, "org.member.remove",
        organization=org_id, resource_type="organization_member", resource_id=user_id,
    )


@router.patch(
    "/{org_id}/members/{user_id}/role",
    response_model=dict,
    summary="Change a member's role",
    description="Updates the role for a given member. Requires `roles:manage` permission.",
)
async def change_member_role(
    org_id: UUID,
    user_id: UUID,
    role_id: UUID = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("roles:manage")),
) -> dict:
    _assert_org_member(current_user, org_id)
    repo = _org_repo()
    await repo.change_member_role(db, org_id, user_id, role_id, current_user.id)
    await audit_service.log(
        db, "org.member.role_change",
        organization=org_id, resource_type="organization_member", resource_id=user_id,
        metadata={"new_role_id": str(role_id)},
    )
    return {"message": "Member role updated."}


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/roles",
    response_model=list[RoleResponse],
    summary="List roles in the organization",
)
async def list_roles(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> list[RoleResponse]:
    _assert_org_member(current_user, org_id)
    from ..models.organization import Role, RolePermission
    stmt = (
        select(Role)
        .where(Role.organization_id == org_id)
        .options(
            selectinload(Role.role_permissions).joinedload(RolePermission.permission)
        )
        .order_by(Role.name)
    )
    result = await db.execute(stmt)
    roles = list(result.scalars().unique().all())
    return [
        RoleResponse(
            id=r.id,
            organization_id=r.organization_id,
            name=r.name,
            slug=r.slug,
            description=getattr(r, "description", None),
            is_system=getattr(r, "is_system", False),
            tier=getattr(r, "tier", None),
            permissions=[
                PermissionResponse(
                    id=rp.permission.id,
                    name=rp.permission.name,
                    slug=rp.permission.slug,
                    description=getattr(rp.permission, "description", None),
                    category=getattr(rp.permission, "category", ""),
                )
                for rp in r.role_permissions
                if rp.permission
            ],
        )
        for r in roles
    ]


@router.post(
    "/{org_id}/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom role",
    description="Creates a new role for the organization. Requires `roles:manage` permission.",
)
async def create_role(
    org_id: UUID,
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("roles:manage")),
) -> RoleResponse:
    _assert_org_member(current_user, org_id)
    from ..models.organization import Permission, Role, RolePermission
    # Check slug uniqueness
    existing = await db.execute(
        select(Role).where(and_(Role.organization_id == org_id, Role.slug == payload.slug))
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message=f"A role with slug '{payload.slug}' already exists in this organization.")

    role = Role(
        organization_id=org_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        is_system=False,
        tier="viewer",
    )
    db.add(role)
    await db.flush()

    for perm_id in payload.permission_ids:
        rp = RolePermission(role_id=role.id, permission_id=perm_id)
        db.add(rp)
    await db.flush()
    await db.refresh(role)

    await audit_service.log(db, "role.create", organization=org_id, resource_type="role", resource_id=role.id)
    return RoleResponse(
        id=role.id,
        organization_id=role.organization_id,
        name=role.name,
        slug=role.slug,
        description=role.description,
        is_system=False,
        tier=None,
        permissions=[],
    )


@router.patch(
    "/{org_id}/roles/{role_id}",
    response_model=RoleResponse,
    summary="Update a role",
    description="Updates a custom role's name/description/permissions. System roles cannot be modified. Requires `roles:manage`.",
)
async def update_role(
    org_id: UUID,
    role_id: UUID,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("roles:manage")),
) -> RoleResponse:
    _assert_org_member(current_user, org_id)
    from ..models.organization import Role, RolePermission
    stmt = select(Role).where(and_(Role.id == role_id, Role.organization_id == org_id))
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError(message="Role not found.")
    if role.is_system:
        raise AuthorizationError(message="System roles cannot be modified.")

    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    db.add(role)

    if payload.permission_ids is not None:
        # Replace all permissions
        del_stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        del_result = await db.execute(del_stmt)
        for rp in del_result.scalars().all():
            await db.delete(rp)
        for perm_id in payload.permission_ids:
            db.add(RolePermission(role_id=role_id, permission_id=perm_id))

    await db.flush()
    await audit_service.log(db, "role.update", organization=org_id, resource_type="role", resource_id=role_id)
    return RoleResponse(
        id=role.id, organization_id=role.organization_id,
        name=role.name, slug=role.slug, description=role.description,
        is_system=False, tier=None, permissions=[],
    )


@router.delete(
    "/{org_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom role",
    description="Deletes a custom role. System roles cannot be deleted. Requires `roles:manage`.",
)
async def delete_role(
    org_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("roles:manage")),
) -> None:
    _assert_org_member(current_user, org_id)
    from ..models.organization import Role
    stmt = select(Role).where(and_(Role.id == role_id, Role.organization_id == org_id))
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError(message="Role not found.")
    if role.is_system:
        raise AuthorizationError(message="System roles cannot be deleted.")
    await db.delete(role)
    await db.flush()
    await audit_service.log(db, "role.delete", organization=org_id, resource_type="role", resource_id=role_id)


# ---------------------------------------------------------------------------
# Permissions catalogue
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/permissions",
    response_model=list[PermissionResponse],
    summary="List available permissions",
    description="Returns all permission definitions available for role assignment.",
)
async def list_permissions(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> list[PermissionResponse]:
    _assert_org_member(current_user, org_id)
    from ..models.organization import Permission
    result = await db.execute(select(Permission).order_by(Permission.category, Permission.name))
    perms = list(result.scalars().all())
    return [
        PermissionResponse(
            id=p.id, name=p.name, slug=p.slug,
            description=getattr(p, "description", None),
            category=getattr(p, "category", ""),
        )
        for p in perms
    ]


# ---------------------------------------------------------------------------
# Helpers — tenant isolation guards (never trust org_id from frontend)
# ---------------------------------------------------------------------------

def _assert_org_member(user: UserLike, org_id: UUID) -> None:
    """Ensure user belongs to the requested org. Owners bypass this check."""
    user_org = getattr(user, "organization_id", None)
    if user_org is None:
        raise AuthorizationError(message="You are not a member of any organization.")
    if str(user_org) != str(org_id):
        # Do not reveal whether the org exists
        raise NotFoundError(message="Organization not found.")


def _assert_is_owner(user: UserLike) -> None:
    """Ensure user has the 'owner' role."""
    roles = getattr(user, "roles", []) or []
    if "owner" not in roles:
        raise AuthorizationError(message="Only the organization owner can perform this action.")
