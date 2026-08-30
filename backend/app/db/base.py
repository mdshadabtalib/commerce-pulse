from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

if TYPE_CHECKING:
    UUID_T = Any
else:
    UUID_T = UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
        index=True,
        sort_order=900,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
        index=True,
        sort_order=901,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        sort_order=902,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
        sort_order=903,
    )

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = utc_now()

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None


class OrganizationScopedMixin:
    @declared_attr
    @classmethod
    def organization_id(cls) -> Mapped[UUID_T]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            sort_order=-999,
        )


class CreatedByMixin:
    @declared_attr
    @classmethod
    def created_by_id(cls) -> Mapped[Optional[UUID_T]]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            sort_order=-998,
        )

    @declared_attr
    @classmethod
    def updated_by_id(cls) -> Mapped[Optional[UUID_T]]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            sort_order=-997,
        )


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
        sort_order=-1000,
    )

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                result[col.name] = value.isoformat()
            elif isinstance(value, UUID):
                result[col.name] = str(value)
            else:
                result[col.name] = value
        return result

    def update_from_dict(self, data: dict[str, Any], *, ignore_keys: set[str] | None = None) -> None:
        ignore = ignore_keys or {"id", "created_at", "updated_at", "organization_id"}
        for key, value in data.items():
            if key in ignore:
                continue
            if hasattr(self, key):
                setattr(self, key, value)
