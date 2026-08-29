from __future__ import annotations

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from ..core.logging import get_logger
from .base import BaseRepository

if TYPE_CHECKING:
    from ..models.dataset import Dataset, DatasetColumn, ImportJob

logger = get_logger(__name__)


class DatasetRepository(BaseRepository):
    async def get_by_checksum(
        self,
        db: AsyncSession,
        organization_id: UUID,
        checksum: str,
    ) -> "Dataset | None":
        stmt = select(self.model).where(
            and_(
                self.model.organization_id == organization_id,
                self.model.checksum == checksum,
            )
        )
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_org(
        self,
        db: AsyncSession,
        org_id: UUID,
        params: Any = None,
        **filters: Any,
    ) -> Any:
        filters["organization_id"] = org_id
        return await self.get_multi(db, params, **filters)

    async def update_status(
        self,
        db: AsyncSession,
        dataset_id: UUID,
        status: str,
        **extra: Any,
    ) -> None:
        stmt = select(self.model).where(self.model.id == dataset_id)
        result = await db.execute(stmt)
        dataset = result.scalar_one_or_none()
        if dataset:
            dataset.status = status
            for key, value in extra.items():
                if hasattr(dataset, key):
                    setattr(dataset, key, value)
            db.add(dataset)
            await db.flush()
            logger.info(
                "Updated dataset status.",
                extra={"dataset_id": str(dataset_id), "status": status},
            )

    async def record_import_completion(
        self,
        db: AsyncSession,
        dataset_id: UUID,
        import_summary: dict[str, Any],
    ) -> None:
        stmt = select(self.model).where(self.model.id == dataset_id)
        result = await db.execute(stmt)
        dataset = result.scalar_one_or_none()
        if dataset:
            dataset.status = import_summary.get("status", getattr(dataset, "status", "COMPLETED"))
            dataset.last_imported_at = import_summary.get("completed_at")
            if hasattr(dataset, "row_count") and "rows_imported" in import_summary:
                dataset.row_count = import_summary["rows_imported"]
            if hasattr(dataset, "import_metadata"):
                dataset.import_metadata = import_summary
            db.add(dataset)
            await db.flush()

    async def create_column_mapping(
        self,
        db: AsyncSession,
        dataset_id: UUID,
        columns: list[dict[str, Any]],
    ) -> list[Any]:
        from ..models.dataset import DatasetColumn

        created = []
        for col in columns:
            col_data = dict(col)
            col_data["dataset_id"] = dataset_id
            db_col = DatasetColumn(**col_data)
            db.add(db_col)
            created.append(db_col)
        await db.flush()
        for c in created:
            await db.refresh(c)
        logger.info(
            "Created column mapping for dataset.",
            extra={"dataset_id": str(dataset_id), "column_count": len(created)},
        )
        return created
