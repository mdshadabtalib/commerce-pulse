from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .common import TimestampModel, UUIDModel


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = None
    phone: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip() if v else v

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = None
    phone: str | None = None

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class UserResponse(UUIDModel, TimestampModel):
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    status: UserStatus
    email_verified_at: datetime | None = None
    last_login_at: datetime | None = None
