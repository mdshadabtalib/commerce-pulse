from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .user import UserResponse


class PasswordValidator:
    MIN_LENGTH = 12
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> str:
        if len(password) < cls.MIN_LENGTH or len(password) > cls.MAX_LENGTH:
            raise ValueError(f"Password must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
            raise ValueError("Password must contain at least one special character")
        return password


class UserRegister(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    organization_name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("full_name", "organization_name")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return PasswordValidator.validate(v)


class UserLogin(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    refresh_token: str


class EmailRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    token: str
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return PasswordValidator.validate(v)


class PasswordChange(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return PasswordValidator.validate(v)


class EmailVerifyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    token: str


LoginResponse = TokenResponse
