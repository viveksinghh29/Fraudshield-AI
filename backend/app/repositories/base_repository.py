"""
Generic base repository — typed CRUD + pagination over any ORM model.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: uuid.UUID) -> ModelType | None:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, id: uuid.UUID) -> ModelType:
        instance = await self.get(id)
        if instance is None:
            raise NotFoundError(
                f"{self.model.__name__} with id={id} not found",
                details={"resource": self.model.__name__, "id": str(id)},
            )
        return instance

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: Any = None,
    ) -> tuple[list[ModelType], int]:
        """Returns (items, total_count) for a filtered, paginated query."""
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is None:
                    continue
                column = getattr(self.model, field)
                query = query.where(column == value)
                count_query = count_query.where(column == value)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset((page - 1) * page_size).limit(page_size)

        total = (await self.session.execute(count_query)).scalar_one()
        items = (await self.session.execute(query)).scalars().all()
        return list(items), total

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, **kwargs: Any) -> ModelType:
        instance = await self.get_or_404(id)
        for field, value in kwargs.items():
            setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> None:
        await self.get_or_404(id)  # raise NotFoundError if it doesn't exist
        await self.session.execute(sa_delete(self.model).where(self.model.id == id))
        await self.session.flush()
