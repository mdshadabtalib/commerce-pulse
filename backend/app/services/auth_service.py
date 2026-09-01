from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import (
    AuthenticationError,
    ConflictError,
    InactiveUserError,
    InvalidTokenError,
    NotFoundError,
    ValidationError,
)
from ..core.logging import get_logger
from ..core.security import (
    TOKEN_TYPE_EMAIL_VERIFICATION,
    TOKEN_TYPE_PASSWORD_RESET,
    jwt_security,
    password_security,
)
from ..repositories.user_repository import UserRepository
from ..repositories.organization_repository import OrganizationRepository
from .audit_service import AuditService
from .rbac_service import RBACService

if TYPE_CHECKING:
    from ..models.user import User
    from ..models.organization import Organization

logger = get_logger(__name__)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID  # Internal; API layer builds full UserResponse


class TokenBlacklist:
    _tokens: dict[str, float] = {}

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        exp = cls._tokens.get(jti)
        if exp:
            now = datetime.now(timezone.utc).timestamp()
            if now < exp:
                return True
            cls._tokens.pop(jti, None)
        return False

    @classmethod
    def add(cls, jti: str, exp_timestamp: int | float) -> None:
        cls._tokens[jti] = float(exp_timestamp)


class AuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository(None)  # type: ignore
        self.org_repo = OrganizationRepository(None)  # type: ignore
        self._audit: AuditService | None = None
        self._rbac: RBACService | None = None

    @property
    def audit(self) -> AuditService:
        if self._audit is None:
            from . import audit_service
            self._audit = audit_service
        return self._audit

    @property
    def rbac(self) -> RBACService:
        if self._rbac is None:
            from . import rbac_service
            self._rbac = rbac_service
        return self._rbac

    def _init_repos(self, db: AsyncSession) -> None:
        from ..models.user import User
        from ..models.organization import Organization
        self.user_repo = UserRepository(User)
        self.org_repo = OrganizationRepository(Organization)

    async def register(
        self,
        db: AsyncSession,
        user_register_in: Any,
        *,
        ip_address: str | None = None,
    ) -> tuple["User", "Organization | None"]:
        from ..models.user import User, UserStatus

        self._init_repos(db)
        data = user_register_in.model_dump(exclude_unset=True) if isinstance(user_register_in, BaseModel) else dict(user_register_in)
        email = (data.get("email") or "").lower().strip()
        if not email:
            raise ValidationError(message="Email is required.")

        existing = await self.user_repo.get_by_email(db, email)
        if existing:
            raise ConflictError(
                message="An account with this email already exists.",
                details={"email": email},
            )

        password = data.pop("password", None)
        if not password:
            raise ValidationError(message="Password is required.")
        password_hash = password_security.hash(password)

        org_name = data.pop("organization_name", None) or data.pop("org_name", None)

        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=data.get("full_name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or None,
            status=UserStatus.PENDING_VERIFICATION,
            email_verified_at=None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        org = None
        if org_name:
            await self.rbac.populate_default_permissions(db)
            org = await self.org_repo.create_with_owner(db, {"name": org_name}, user.id)

        verification_token = jwt_security.create_email_verification_token(str(user.id))
        try:
            from ..core.celery_app import celery_app
            if celery_app and not settings.CELERY_TASK_ALWAYS_EAGER:
                celery_app.send_task(
                    "emails.send",
                    args=[[email], "Verify Your Email", "email_verification", {
                        "token": verification_token,
                        "user_id": str(user.id),
                    }],
                    queue="emails",
                )
        except Exception as exc:
            logger.warning(
                "Failed to queue verification email.",
                extra={"user_id": str(user.id), "error": str(exc)},
            )

        await self.audit.log(
            db,
            "user.register",
            user=user,
            organization=org,
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
            metadata={"email": email, "org_created": org is not None},
        )

        logger.info("User registered successfully.", extra={"user_id": str(user.id), "org_id": str(org.id) if org else None})
        return user, org

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        from ..models.user import UserStatus

        self._init_repos(db)
        user = await self.user_repo.authenticate(db, email, password)
        if not user:
            await self.audit.log(
                db,
                "auth.login_failed",
                ip_address=ip,
                user_agent=user_agent,
                metadata={"email": email, "reason": "invalid_credentials"},
            )
            raise AuthenticationError(message="Invalid email or password.")

        user_status = getattr(user, "status", None)
        if user_status and user_status not in (
            UserStatus.ACTIVE,
            UserStatus.PENDING_VERIFICATION,
        ):
            raise InactiveUserError()

        session_id = str(uuid4())
        access_token = jwt_security.create_access_token(
            str(user.id),
            roles=getattr(user, "roles", []),
            extra_claims={"sid": session_id},
        )
        refresh_token = jwt_security.create_refresh_token(str(user.id), session_id=session_id)

        await self.user_repo.record_login(db, user.id, ip)

        await self.audit.log(
            db,
            "auth.login_success",
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            resource_type="user",
            resource_id=user.id,
            metadata={"session_id": session_id},
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
        )

    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:
        self._init_repos(db)
        try:
            payload = jwt_security.decode_refresh_token(refresh_token)
        except InvalidTokenError:
            raise
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and TokenBlacklist.is_blacklisted(jti):
            raise InvalidTokenError(message="Refresh token has been revoked.")
        if jti and exp:
            TokenBlacklist.add(jti, exp)

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError(message="Token missing subject claim.")
        from ..models.user import User
        user_stmt = select(User).where(User.id == UUID(user_id))
        if hasattr(User, "is_deleted"):
            user_stmt = user_stmt.where(User.is_deleted == False)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise AuthenticationError(message="User not found.")

        from ..models.user import User, UserStatus
        user_status = getattr(user, "status", None)
        if user_status and user_status not in (
            UserStatus.ACTIVE,
            UserStatus.PENDING_VERIFICATION,
        ):
            raise InactiveUserError()

        session_id = str(uuid4())
        new_access = jwt_security.create_access_token(
            str(user.id),
            roles=getattr(user, "roles", []),
            extra_claims={"sid": session_id},
        )
        new_refresh = jwt_security.create_refresh_token(str(user.id), session_id=session_id)

        await self.audit.log(
            db,
            "auth.token_refresh",
            user=user,
            resource_type="user",
            resource_id=user.id,
            metadata={"old_jti": jti, "new_session_id": session_id},
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
        )

    async def logout(
        self,
        db: AsyncSession,
        access_token: str,
        *,
        user: "User | None" = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        try:
            payload = jwt_security.decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                TokenBlacklist.add(jti, exp)
            user_id = payload.get("sub")
        except InvalidTokenError:
            return

        if user_id:
            await self.audit.log(
                db,
                "auth.logout",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type="user",
                resource_id=user_id,
                metadata={"jti": jti},
            )

    async def request_password_reset(
        self,
        db: AsyncSession,
        email: str,
        *,
        request_id: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        self._init_repos(db)
        user = await self.user_repo.get_by_email(db, email)
        if not user:
            logger.info(
                "Password reset requested for non-existent email (silent return).",
                extra={"email": email},
            )
            return

        token = jwt_security.create_password_reset_token(
            str(user.id),
            extra_claims={"req_id": request_id or str(uuid4())},
        )
        try:
            from ..core.celery_app import celery_app
            if celery_app:
                celery_app.send_task(
                    "emails.send",
                    args=[[email], "Reset Your Password", "password_reset", {
                        "token": token,
                        "user_id": str(user.id),
                    }],
                    queue="emails",
                )
        except Exception as exc:
            logger.warning(
                "Failed to queue password reset email.",
                extra={"user_id": str(user.id), "error": str(exc)},
            )

        await self.audit.log(
            db,
            "auth.password_reset_requested",
            user=user,
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
        )

    async def confirm_password_reset(
        self,
        db: AsyncSession,
        token: str,
        new_password: str,
        *,
        ip_address: str | None = None,
    ) -> None:
        self._init_repos(db)
        try:
            payload = jwt_security.decode_token(token, expected_type=TOKEN_TYPE_PASSWORD_RESET)
        except InvalidTokenError:
            raise
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and TokenBlacklist.is_blacklisted(jti):
            raise InvalidTokenError(message="Reset token has already been used.")
        if jti and exp:
            TokenBlacklist.add(jti, exp)

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()
        new_hash = password_security.hash(new_password)
        await self.user_repo.update_password(db, UUID(user_id), new_hash)

        await self.audit.log(
            db,
            "auth.password_reset_confirmed",
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
            metadata={"password_changed": True, "invalidated_sessions": False},
        )

    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_pwd: str,
        new_pwd: str,
        *,
        ip_address: str | None = None,
    ) -> None:
        self._init_repos(db)
        from ..models.user import User
        user_stmt = select(User).where(User.id == user_id)
        if hasattr(User, "is_deleted"):
            user_stmt = user_stmt.where(User.is_deleted == False)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError(message="User not found.")

        verified, _ = password_security.verify(current_pwd, user.hashed_password)
        if not verified:
            raise AuthenticationError(message="Current password is incorrect.")

        if current_pwd == new_pwd:
            raise ValidationError(message="New password must be different from current password.")

        new_hash = password_security.hash(new_pwd)
        await self.user_repo.update_password(db, user_id, new_hash)

        await self.audit.log(
            db,
            "auth.password_changed",
            user=user,
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
        )

    async def verify_email(
        self,
        db: AsyncSession,
        token: str,
        *,
        ip_address: str | None = None,
    ) -> "User":
        self._init_repos(db)
        try:
            payload = jwt_security.decode_token(token, expected_type=TOKEN_TYPE_EMAIL_VERIFICATION)
        except InvalidTokenError:
            raise
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and TokenBlacklist.is_blacklisted(jti):
            raise InvalidTokenError(message="Verification token has already been used.")
        if jti and exp:
            TokenBlacklist.add(jti, exp)

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()
        await self.user_repo.verify_email(db, UUID(user_id))

        from ..models.user import User
        user = await self.user_repo.get(db, UUID(user_id))
        if not user:
            raise NotFoundError(message="User not found.")

        await self.audit.log(
            db,
            "auth.email_verified",
            user=user,
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
        )
        return user
