"""Resolves and caches the active model Predictor, reloading only when the active model version changes."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ModelNotLoadedError
from app.ml.engine.predictor import Predictor
from app.repositories.model_version_repository import ModelVersionRepository

_cached_predictor: Predictor | None = None
_cached_model_version_id: uuid.UUID | None = None


class ModelService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ModelVersionRepository(session)

    async def get_active_predictor(self):
        """Returns (predictor, active_model_version) for whichever model is currently active."""
        global _cached_predictor, _cached_model_version_id

        active = await self.repo.get_active()
        if active is None:
            raise ModelNotLoadedError(
                "No active model version found. Train and register a model first "
                "(see app.ml.pipeline.train)."
            )

        if _cached_predictor is None or _cached_model_version_id != active.id:
            _cached_predictor = Predictor(active.artifact_path)
            _cached_model_version_id = active.id

        return _cached_predictor, active

    @staticmethod
    def clear_cache() -> None:
        """Used by tests, and by /model/activate (later phase) to force a reload."""
        global _cached_predictor, _cached_model_version_id
        _cached_predictor = None
        _cached_model_version_id = None
