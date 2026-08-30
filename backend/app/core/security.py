from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError as Argon2VerifyMismatchError
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings
from .errors import (
    CSRFValidationError,
    ExpiredTokenError,
    InvalidTokenError,
    PasswordValidationError,
    RateLimitExceededError,
    ValidationError,
)
from .logging import get_logger

logger = get_logger(__name__)

_ALPHABET = string.ascii_letters + string.digits


class PasswordSecurity:
    _argon2: Argon2Hasher
    _bcrypt_context: CryptContext
    _argon2_identifier: str = "$argon2id$"

    def __init__(self) -> None:
        self._argon2 = Argon2Hasher(
            time_cost=4,
            memory_cost=65536,
            parallelism=2,
            hash_len=32,
            salt_len=16,
        )
        self._bcrypt_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,
        )

    def hash(self, password: str) -> str:
        if not password or not isinstance(password, str):
            raise PasswordValidationError("Password must be a non-empty string.")
        self._validate_password_strength(password)
        return self._argon2.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> tuple[bool, Optional[str]]:
        if not plain_password or not hashed_password:
            return False, None
        needs_rehash = False
        verified = False

        if hashed_password.startswith(self._argon2_identifier):
            try:
                self._argon2.verify(hashed_password, plain_password)
                verified = True
                needs_rehash = self._argon2.check_needs_rehash(hashed_password)
            except Argon2VerifyMismatchError:
                verified = False
            except Exception as exc:
                logger.warning("Argon2 verification failed unexpectedly: %s", exc)
                verified = False
        else:
            try:
                verified = self._bcrypt_context.verify(plain_password, hashed_password)
                needs_rehash = verified
            except Exception as exc:
                logger.warning("Bcrypt verification failed: %s", exc)
                verified = False

        new_hash = None
        if verified and needs_rehash:
            try:
                new_hash = self._argon2.hash(plain_password)
            except Exception as exc:
                logger.error("Failed to rehash password during migration: %s", exc)

        return verified, new_hash

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        issues: list[str] = []
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long.")
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
            issues.append("Password must contain at least one special character.")
        if issues:
            raise PasswordValidationError(
                message="Password does not meet strength requirements.",
                details={"issues": issues},
            )


password_security = PasswordSecurity()

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"


class JWTSecurity:
    def __init__(self) -> None:
        self._secret = settings.SECRET_KEY.get_secret_value()
        self._algorithm = settings.ALGORITHM

    def _build_token(
        self,
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": str(subject),
            "type": token_type,
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4()),
            "iss": settings.APP_NAME,
            "exp": int((now + expires_delta).timestamp()),
            "nbf": int(now.timestamp()),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_access_token(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        roles: Optional[list[str]] = None,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        claims = dict(extra_claims or {})
        if organization_id:
            claims["org_id"] = organization_id
        if roles:
            claims["roles"] = roles
        return self._build_token(
            subject=user_id,
            token_type=TOKEN_TYPE_ACCESS,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            extra_claims=claims,
        )

    def create_refresh_token(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        claims = dict(extra_claims or {})
        if session_id:
            claims["sid"] = session_id
        return self._build_token(
            subject=user_id,
            token_type=TOKEN_TYPE_REFRESH,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            extra_claims=claims,
        )

    def create_password_reset_token(self, user_id: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
        return self._build_token(
            subject=user_id,
            token_type=TOKEN_TYPE_PASSWORD_RESET,
            expires_delta=timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
            extra_claims=extra_claims,
        )

    def create_email_verification_token(self, user_id: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
        return self._build_token(
            subject=user_id,
            token_type=TOKEN_TYPE_EMAIL_VERIFICATION,
            expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
            extra_claims=extra_claims,
        )

    def decode_token(self, token: str, expected_type: Optional[str] = None) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=settings.APP_NAME,
                options={
                    "require": ["exp", "iat", "sub", "type", "jti", "iss"],
                    "verify_aud": False,
                },
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenError() from exc
        except JWTClaimsError as exc:
            raise InvalidTokenError(message="Token claims validation failed.") from exc
        except JWTError as exc:
            raise InvalidTokenError() from exc

        if expected_type and payload.get("type") != expected_type:
            raise InvalidTokenError(
                message=f"Invalid token type. Expected '{expected_type}'.",
                details={"expected": expected_type, "got": payload.get("type")},
            )
        return payload

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return self.decode_token(token, expected_type=TOKEN_TYPE_ACCESS)

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        return self.decode_token(token, expected_type=TOKEN_TYPE_REFRESH)


jwt_security = JWTSecurity()


class CSRFManager:
    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def generate_signed_token(session_id: str, expires_minutes: int = 60) -> str:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=expires_minutes)
        raw = f"{session_id}|{int(expires.timestamp())}|{secrets.token_hex(16)}"
        key = settings.CSRF_SECRET_KEY.get_secret_value().encode("utf-8")
        signature = hmac.new(key, raw.encode("utf-8"), hashlib.sha256).digest()
        combined = raw.encode("utf-8") + b"|" + signature
        return base64.urlsafe_b64encode(combined).decode("utf-8").rstrip("=")

    @staticmethod
    def validate_signed_token(token: str, session_id: str) -> bool:
        try:
            padding = "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(token + padding)
            parts = decoded.rsplit(b"|", 1)
            if len(parts) != 2:
                raise CSRFValidationError("Malformed CSRF token.")
            raw_bytes, provided_signature = parts
            raw = raw_bytes.decode("utf-8")
            key = settings.CSRF_SECRET_KEY.get_secret_value().encode("utf-8")
            expected_signature = hmac.new(key, raw_bytes, hashlib.sha256).digest()
            if not hmac.compare_digest(provided_signature, expected_signature):
                raise CSRFValidationError("Invalid CSRF token signature.")
            raw_parts = raw.split("|")
            if len(raw_parts) != 3 or raw_parts[0] != session_id:
                raise CSRFValidationError("CSRF token session mismatch.")
            expires_at = int(raw_parts[1])
            if datetime.now(timezone.utc).timestamp() > expires_at:
                raise CSRFValidationError("CSRF token has expired.")
            return True
        except CSRFValidationError:
            raise
        except Exception as exc:
            logger.warning("CSRF validation failed: %s", exc)
            raise CSRFValidationError() from exc


def build_rate_limiter() -> Limiter:
    storage_uri = settings.REDIS_URL if settings.RATE_LIMIT_STORAGE == "redis" else None
    try:
        # SlowAPI delegates storage construction to its ``storage_uri``
        # parameter.  It has no public ``RedisStorage`` wrapper.
        limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
    except Exception as exc:
        logger.warning("Failed to initialize rate limiter storage, falling back to in-memory: %s", exc)
        limiter = Limiter(key_func=get_remote_address)
    return limiter


class SecureRandom:
    @staticmethod
    def token_urlsafe(nbytes: int = 32) -> str:
        return secrets.token_urlsafe(nbytes)

    @staticmethod
    def token_hex(nbytes: int = 32) -> str:
        return secrets.token_hex(nbytes)

    @staticmethod
    def api_key(prefix: str = "cp_", length: int = 48) -> str:
        body = "".join(secrets.choice(_ALPHABET) for _ in range(max(16, length - len(prefix))))
        return f"{prefix}{body}"

    @staticmethod
    def numeric_otp(length: int = 6) -> str:
        if length < 4 or length > 12:
            raise ValidationError("OTP length must be between 4 and 12 digits.")
        return "".join(secrets.choice(string.digits) for _ in range(length))
