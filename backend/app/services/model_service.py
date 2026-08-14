"""
ModelService — resolves "the currently active model" to a loaded,
ready-to-use Predictor, cached in-process so repeated prediction
requests don't re-deserialize the joblib artifact from disk every time.

The cache is keyed by model_version_id: each call does one cheap DB
query to check which version is active, and only reloads the artifact
from disk if that id has changed since the last call (e.g. an admin
just activated a newly trained model via /model/activate in a later
phase). This keeps hot-path prediction requests fast while still
picking up a newly activated model without requiring an app restart.
"""

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
