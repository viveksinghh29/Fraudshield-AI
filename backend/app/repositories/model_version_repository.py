"""ModelVersionRepository — model registry lookups and activation."""

from sqlalchemy import select, update

from app.models.model_version import ModelVersion
from app.repositories.base_repository import BaseRepository


class ModelVersionRepository(BaseRepository[ModelVersion]):
    model = ModelVersion

    async def get_active(self) -> ModelVersion | None:
        result = await self.session.execute(
            select(ModelVersion).where(ModelVersion.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_by_tag(self, version_tag: str) -> ModelVersion | None:
        result = await self.session.execute(
            select(ModelVersion).where(ModelVersion.version_tag == version_tag)
        )
        return result.scalar_one_or_none()

    async def activate(self, model_version_id) -> ModelVersion:
        """
        Deactivates every other version and activates the given one, in a
        single flush, so there's never a window where zero or multiple
        versions are marked active.
        """
        await self.session.execute(
            update(ModelVersion).where(ModelVersion.id != model_version_id).values(is_active=False)
        )
        return await self.update(model_version_id, is_active=True)
