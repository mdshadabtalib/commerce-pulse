from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ..core.config import settings
from ..core.errors import NotFoundError
from ..core.logging import get_logger
from ..db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .schemas import PaginatedResponse, ListQueryParams

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ListQueryParams(BaseModel):
    skip: int = 0
    limit: int = settings.PAGE_SIZE_DEFAULT
    order_by: Optional[str] = None
    order_dir: str = "desc"
    search: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    model: type[ModelType]

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: UUID) -> ModelType:
        obj = await self.get(db, id)
        if obj is None:
            raise NotFoundError(
                message=f"{self.model.__name__} not found.",
                details={"id": str(id), "resource": self.model.__name__},
            )
        return obj

    async def get_multi(
        self,
        db: AsyncSession,
        params: ListQueryParams | None = None,
        **filters: Any,
    ) -> PaginatedResponse:
        params = params or ListQueryParams()
        conditions = []
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        if hasattr(self.model, "is_deleted"):
            conditions.append(self.model.is_deleted == False)

        where_clause = and_(*conditions) if conditions else None

        count_stmt = select(func.count()).select_from(self.model)
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one() or 0

        stmt = select(self.model)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        if params.order_by and hasattr(self.model, params.order_by):
            from sqlalchemy import desc, asc
            order_func = desc if params.order_dir.lower() == "desc" else asc
            stmt = stmt.order_by(order_func(getattr(self.model, params.order_by)))
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(params.skip).limit(min(params.limit, settings.PAGE_SIZE_MAX))

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        per_page = min(params.limit, settings.PAGE_SIZE_MAX)
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        page = (params.skip // per_page) + 1 if per_page > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType | dict[str, Any],
        *,
        created_by_id: UUID | None = None,
    ) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else dict(obj_in)
        if created_by_id is not None and hasattr(self.model, "created_by_id"):
            data["created_by_id"] = created_by_id
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        logger.info(
            "Created %s.",
            self.model.__name__,
            extra={"resource_id": str(db_obj.id), "created_by": str(created_by_id) if created_by_id else None},
        )
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
        *,
        updated_by_id: UUID | None = None,
    ) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else dict(obj_in)
        if updated_by_id is not None and hasattr(self.model, "updated_by_id"):
            data["updated_by_id"] = updated_by_id
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        logger.info(
            "Updated %s.",
            self.model.__name__,
            extra={"resource_id": str(db_obj.id), "updated_by": str(updated_by_id) if updated_by_id else None},
        )
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        id: UUID,
        *,
        hard: bool = False,
    ) -> None:
        db_obj = await self.get_or_404(db, id)
        if hard:
            await db.delete(db_obj)
            logger.info(
                "Hard deleted %s.",
                self.model.__name__,
                extra={"resource_id": str(id)},
            )
        elif isinstance(db_obj, SoftDeleteMixin):
            db_obj.soft_delete()
            db.add(db_obj)
            logger.info(
                "Soft deleted %s.",
                self.model.__name__,
                extra={"resource_id": str(id)},
            )
        else:
            await db.delete(db_obj)
            logger.info(
                "Deleted %s (no soft delete support).",
                self.model.__name__,
                extra={"resource_id": str(id)},
            )
        await db.flush()

    async def exists(self, db: AsyncSession, **filters: Any) -> bool:
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        if hasattr(self.model, "is_deleted"):
            conditions.append(self.model.is_deleted == False)
        stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        result = await db.execute(stmt)
        count = result.scalar_one() or 0
        return count > 0
