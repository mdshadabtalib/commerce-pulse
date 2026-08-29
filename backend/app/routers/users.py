"""Users router — current user profile management and admin user listing."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import (
    get_current_active_user,
    get_db,
    require_permissions,
    UserLike,
)
from ..core.errors import NotFoundError
from ..core.logging import get_logger
from ..repositories.base import ListQueryParams
from ..repositories.user_repository import UserRepository
from ..schemas.user import UserResponse, UserUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_repo() -> UserRepository:
    from ..models.user import User
    return UserRepository(User)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> UserResponse:
    repo = _get_user_repo()
    user = await repo.get(db, current_user.id)
    if not user:
        raise NotFoundError(message="User not found.")
    return UserResponse.model_validate(user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Updates the authenticated user's name, avatar, or phone. Email changes require re-verification and are not supported here.",
)
async def update_current_user(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> UserResponse:
    repo = _get_user_repo()
    user = await repo.get(db, current_user.id)
    if not user:
        raise NotFoundError(message="User not found.")
    updated = await repo.update(db, user, payload)
    return UserResponse.model_validate(updated)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List users (admin only)",
    description="Returns a paginated list of all users. Requires `users:manage` permission.",
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: UserLike = Depends(require_permissions("users:manage")),
) -> list[UserResponse]:
    repo = _get_user_repo()
    result = await repo.get_multi(db, ListQueryParams(skip=skip, limit=limit))
    return [UserResponse.model_validate(u) for u in result.items]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (admin only)",
    description="Returns a specific user's profile. Requires `users:manage` permission.",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UserLike = Depends(require_permissions("users:manage")),
) -> UserResponse:
    repo = _get_user_repo()
    user = await repo.get_or_404(db, user_id)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a user (admin only)",
    description="Suspends a user account. Requires `users:manage` permission.",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(require_permissions("users:manage")),
) -> None:
    from ..models.user import UserStatus
    repo = _get_user_repo()
    user = await repo.get_or_404(db, user_id)
    if str(user.id) == str(current_user.id):
        from ..core.errors import ValidationError
        raise ValidationError(message="You cannot deactivate your own account.")
    await repo.update(db, user, {"status": UserStatus.SUSPENDED})
