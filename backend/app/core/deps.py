from __future__ import annotations

from contextvars import ContextVar
from typing import Any, AsyncGenerator, Callable, Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .config import settings
from .errors import (
    AuthenticationError,
    InactiveUserError,
    MissingTokenError,
    PermissionRequiredError,
    RoleRequiredError,
    TenantIsolationError,
)
from .logging import get_logger
from .security import jwt_security
from ..db.session import async_session_factory

logger = get_logger(__name__)

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
org_id_var: ContextVar[Optional[str]] = ContextVar("org_id", default=None)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)

oauth2_scheme_strict = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def _set_context(request: Request, user_id: Optional[str], org_id: Optional[str]) -> None:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if org_id:
        org_id_var.set(org_id)


class UserLike:
    id: Any
    is_active: bool
    organization_id: Any
    roles: list[str]
    permissions: list[str]

    def __init__(
        self,
        *,
        id: Any,
        is_active: bool = True,
        organization_id: Any = None,
        roles: Optional[list[str]] = None,
        permissions: Optional[list[str]] = None,
    ) -> None:
        self.id = id
        self.is_active = is_active
        self.organization_id = organization_id
        self.roles = roles or []
        self.permissions = permissions or []


async def _fetch_user_from_token(db: AsyncSession, token_payload: dict[str, Any]) -> UserLike:
    from ..models.organization import OrganizationMember, Permission, Role, RolePermission
    from ..models.user import User, UserStatus

    user_id = token_payload.get("sub")
    if not user_id:
        raise AuthenticationError(message="Token missing subject claim.")

    try:
        user_uuid = UUID(str(user_id))
    except (ValueError, AttributeError):
        raise AuthenticationError(message="Invalid subject claim in token.")

    stmt = (
        select(User)
        .options(
            selectinload(User.organization_memberships).options(
                joinedload(OrganizationMember.role).options(
                    selectinload(Role.role_permissions).joinedload(RolePermission.permission)
                )
            )
        )
        .where(User.id == user_uuid)
    )
    result = await db.execute(stmt)
    user: Optional[User] = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError(message="User not found.")

    is_active = True
    if hasattr(user, "status"):
        is_active = user.status in (UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION)

    active_member: Optional[OrganizationMember] = None
    for member in user.organization_memberships:
        member_status = getattr(member, "status", None)
        status_str = str(member_status) if member_status else ""
        if status_str.upper() in {"ACTIVE", "ACCEPTED"}:
            active_member = member
            break

    organization_id: Optional[Any] = None
    roles: list[str] = []
    permissions: list[str] = []

    if active_member is not None:
        organization_id = active_member.organization_id
        role = getattr(active_member, "role", None)
        if role is not None:
            role_slug = getattr(role, "slug", None)
            if role_slug:
                roles.append(str(role_slug))
            role_perms = getattr(role, "role_permissions", [])
            for rp in role_perms:
                perm = getattr(rp, "permission", None)
                perm_slug = getattr(perm, "slug", None)
                if perm_slug:
                    perm_slug_str = str(perm_slug)
                    if perm_slug_str not in permissions:
                        permissions.append(perm_slug_str)

    return UserLike(
        id=user.id,
        is_active=is_active,
        organization_id=organization_id,
        roles=roles,
        permissions=permissions,
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme_strict),
) -> UserLike:
    if not token:
        raise MissingTokenError()
    payload = jwt_security.decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(message="Token missing subject claim.")
    try:
        user = await _fetch_user_from_token(db, payload)
    except NotImplementedError:
        user = UserLike(
            id=user_id,
            is_active=True,
            organization_id=payload.get("org_id"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
        )
    if str(user.id) != str(user_id):
        raise AuthenticationError(message="Token subject does not match stored user.")
    _set_context(request, str(user.id), str(user.organization_id) if user.organization_id else None)
    return user


async def get_current_active_user(
    current_user: UserLike = Depends(get_current_user),
) -> UserLike:
    if not getattr(current_user, "is_active", True):
        raise InactiveUserError()
    return current_user


def require_roles(*required_roles: str, match_all: bool = False) -> Callable[..., UserLike]:
    async def dependency(user: UserLike = Depends(get_current_active_user)) -> UserLike:
        user_roles = set(getattr(user, "roles", []) or [])
        required = set(required_roles)
        if match_all:
            has_access = required.issubset(user_roles)
        else:
            has_access = bool(required & user_roles)
        if not has_access:
            raise RoleRequiredError(required_roles=list(required_roles))
        return user

    return dependency


def require_permissions(*required_permissions: str, match_all: bool = False) -> Callable[..., UserLike]:
    async def dependency(user: UserLike = Depends(get_current_active_user)) -> UserLike:
        user_perms = set(getattr(user, "permissions", []) or [])
        required = set(required_permissions)
        if match_all:
            has_access = required.issubset(user_perms)
        else:
            has_access = bool(required & user_perms)
        if not has_access:
            raise PermissionRequiredError(required_permissions=list(required_permissions))
        return user

    return dependency


def get_org_from_user(user: UserLike) -> str:
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        raise TenantIsolationError(message="User is not associated with an organization.")
    return str(org_id)


def require_org_match(
    *,
    param_name: str,
    allow_admin_override: bool = False,
    admin_roles: Optional[set[str]] = None,
) -> Callable[..., str]:
    if admin_roles is None:
        admin_roles = {"admin", "owner", "super_admin"}

    async def dependency(
        request: Request,
        user: UserLike = Depends(get_current_active_user),
    ) -> str:
        user_org_id = get_org_from_user(user)
        path_value: Optional[Any] = request.path_params.get(param_name)
        query_value: Optional[Any] = None
        try:
            query_value = request.query_params.get(param_name)
        except Exception:
            pass
        client_org_id = path_value or query_value
        if not client_org_id:
            logger.info(
                "No client organization_id provided in request; using user's org.",
                extra={"request_id": request_id_var.get()},
            )
            return user_org_id
        user_roles = set(getattr(user, "roles", []) or [])
        if str(client_org_id) != str(user_org_id):
            if allow_admin_override and (user_roles & admin_roles):
                logger.info(
                    "Admin user overriding tenant isolation.",
                    extra={
                        "user_id": user_id_var.get(),
                        "roles": list(user_roles),
                        "target_org": client_org_id,
                        "user_org": user_org_id,
                    },
                )
                return str(client_org_id)
            raise TenantIsolationError(
                details={
                    "user_organization_id": user_org_id,
                    "requested_organization_id": str(client_org_id),
                }
            )
        return user_org_id

    return dependency
