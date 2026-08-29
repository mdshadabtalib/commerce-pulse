from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .common import Currency, TimestampModel, UUIDModel
from .user import UserResponse


class OrganizationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    SUSPENDED = "SUSPENDED"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"


class OrganizationSize(str, Enum):
    SOLO = "SOLO"
    STARTUP = "STARTUP"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    ENTERPRISE = "ENTERPRISE"


class RoleTier(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class OrganizationMemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    INACTIVE = "INACTIVE"


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str = Field(min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str = "UTC"
    default_currency: Currency = Currency.USD

    @field_validator("name", "slug")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    logo_url: str | None = None
    website: str | None = None
    timezone: str | None = None
    default_currency: Currency | None = None
    billing_email: EmailStr | None = None
    settings: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class OrganizationResponse(UUIDModel, TimestampModel):
    name: str
    slug: str
    status: OrganizationStatus
    size: OrganizationSize | None = None
    logo_url: str | None = None
    website: str | None = None
    timezone: str
    default_currency: Currency
    billing_email: str | None = None
    settings: dict[str, Any] | None = None


class MemberInvite(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    email: EmailStr
    role_id: UUID | None = None
    role_slug: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("role_slug")
    @classmethod
    def validate_role_slug(cls, v: str | None) -> str | None:
        if v and v not in {"admin", "analyst", "viewer", "owner"}:
            raise ValueError("role_slug must be one of: admin, analyst, viewer, owner")
        return v


class MemberInviteBatch(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    invites: list[MemberInvite] = Field(min_length=1)


class OrganizationMemberCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    user_id: UUID
    role_id: UUID | None = None
    is_owner: bool = False

    @field_validator("is_owner")
    @classmethod
    def validate_owner_role(cls, v: bool, info: Any) -> bool:
        return v


class MemberUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    role_id: UUID | None = None
    is_owner: bool | None = None
    status: OrganizationMemberStatus | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    name: str
    slug: str
    description: str | None = None
    category: str


class RoleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[UUID] = Field(default_factory=list)

    @field_validator("name", "slug")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class RoleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[UUID] | None = None

    @field_validator("name")
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    organization_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    is_system: bool = False
    tier: RoleTier | None = None
    permissions: list[PermissionResponse] = Field(default_factory=list)


class OrganizationMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: UUID
    organization_id: UUID
    user: UserResponse
    role: RoleResponse | None = None
    is_owner: bool = False
    status: OrganizationMemberStatus
    joined_at: datetime | None = None
    last_accessed_at: datetime | None = None


class OrganizationSwitch(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    org_slug: str | None = None
    org_id: UUID | None = None

    @field_validator("org_slug")
    @classmethod
    def strip_slug(cls, v: str | None) -> str | None:
        return v.strip() if v else v
