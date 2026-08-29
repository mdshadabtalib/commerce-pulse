"""Authentication router — register, login, refresh, logout, verify email, password reset/change."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_active_user, get_db, UserLike
from ..core.errors import MissingTokenError
from ..core.logging import get_logger
from ..core.security import jwt_security
from ..schemas.auth import (
    EmailRequest,
    EmailVerifyRequest,
    LoginResponse,
    PasswordChange,
    PasswordResetConfirm,
    RefreshTokenRequest,
    TokenResponse,
    UserRegister,
    UserLogin,
)
from ..schemas.user import UserResponse
from ..services.auth_service import AuthService

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
_auth_service = AuthService()


def _user_to_response(user: Any) -> UserResponse:
    """Map a User ORM object to UserResponse schema."""
    from ..models.user import UserStatus
    return UserResponse(
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


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Creates a new user account and optionally a new organization. "
        "An email verification link is sent asynchronously. "
        "The account is functional but marked PENDING_VERIFICATION until verified."
    ),
    responses={
        201: {"description": "User registered successfully"},
        409: {"description": "Email already in use"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    ip = request.client.host if request.client else None
    user, org = await _auth_service.register(db, payload, ip_address=ip)
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": str(user.id),
        "organization_id": str(org.id) if org else None,
        "email_verification_required": True,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description=(
        "Authenticates a user and returns a JWT access token + refresh token. "
        "Access tokens expire after the configured period (default 30 min). "
        "Use the refresh token endpoint to obtain a new access token."
    ),
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        403: {"description": "Account inactive or suspended"},
    },
)
async def login(
    payload: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token_resp = await _auth_service.login(
        db, payload.email, payload.password, ip=ip, user_agent=user_agent
    )
    # Fetch full user for response
    from ..repositories.user_repository import UserRepository
    from ..models.user import User
    user_repo = UserRepository(User)
    user = await user_repo.get(db, token_resp.user_id)
    return TokenResponse(
        access_token=token_resp.access_token,
        refresh_token=token_resp.refresh_token,
        token_type="bearer",
        expires_in=token_resp.expires_in,
        user=_user_to_response(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description=(
        "Issues a new access token using a valid refresh token. "
        "The old refresh token is invalidated (single-use rotation)."
    ),
    responses={
        200: {"description": "Token refreshed"},
        401: {"description": "Refresh token invalid or revoked"},
    },
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token_resp = await _auth_service.refresh_token(db, payload.refresh_token)
    from ..repositories.user_repository import UserRepository
    from ..models.user import User
    user_repo = UserRepository(User)
    user = await user_repo.get(db, token_resp.user_id)
    return TokenResponse(
        access_token=token_resp.access_token,
        refresh_token=token_resp.refresh_token,
        token_type="bearer",
        expires_in=token_resp.expires_in,
        user=_user_to_response(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (revoke current tokens)",
    description="Revokes the current access token's JTI. Pass the refresh token in the body to also revoke it.",
    responses={204: {"description": "Logged out successfully"}},
)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
    authorization: str | None = Header(default=None),
) -> None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    if token:
        try:
            payload = jwt_security.decode_access_token(token)
            await _auth_service.logout(db, token)
        except Exception:
            pass  # best-effort revocation
    logger.info("User logged out.", extra={"user_id": str(current_user.id)})


@router.post(
    "/verify-email",
    response_model=dict,
    summary="Verify email address",
    description="Activates the user account using the token sent to the registered email address.",
    responses={
        200: {"description": "Email verified"},
        400: {"description": "Token invalid or expired"},
    },
)
async def verify_email(
    payload: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _auth_service.verify_email(db, payload.token)
    return {"message": "Email verified successfully. Your account is now active."}


@router.post(
    "/forgot-password",
    response_model=dict,
    summary="Request a password reset link",
    description=(
        "Sends a password reset link to the given email if an account exists. "
        "Always returns 200 to prevent user enumeration."
    ),
    responses={200: {"description": "Reset email sent (if account exists)"}},
)
async def forgot_password(
    payload: EmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _auth_service.request_password_reset(db, payload.email)
    return {"message": "If an account exists for this email, a password reset link has been sent."}


@router.post(
    "/reset-password",
    response_model=dict,
    summary="Confirm password reset with token",
    description="Resets the user's password using the token from the reset email. Token is single-use.",
    responses={
        200: {"description": "Password reset successful"},
        400: {"description": "Token invalid or expired"},
    },
)
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _auth_service.confirm_password_reset(db, payload.token, payload.new_password)
    return {"message": "Password has been reset successfully. Please login with your new password."}


@router.post(
    "/change-password",
    response_model=dict,
    summary="Change password (authenticated)",
    description="Changes the authenticated user's password. Requires the current password for verification.",
    responses={
        200: {"description": "Password changed"},
        401: {"description": "Current password incorrect"},
    },
)
async def change_password(
    payload: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> dict:
    await _auth_service.change_password(
        db,
        user_id=current_user.id,
        current_pwd=payload.current_password,
        new_pwd=payload.new_password,
    )
    return {"message": "Password changed successfully."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: UserLike = Depends(get_current_active_user),
) -> UserResponse:
    from ..repositories.user_repository import UserRepository
    from ..models.user import User
    user_repo = UserRepository(User)
    user = await user_repo.get(db, current_user.id)
    return _user_to_response(user)
