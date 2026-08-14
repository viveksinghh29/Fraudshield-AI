"""Model metadata endpoint — the currently active model's version, algorithm, and metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.exceptions import ModelNotLoadedError
from app.db.session import get_db
from app.models.user import User
from app.repositories.model_version_repository import ModelVersionRepository
from app.schemas.prediction_schema import ModelInfoResponse

router = APIRouter()


@router.get("/info", response_model=ModelInfoResponse)
async def get_active_model_info(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ModelInfoResponse:
    repo = ModelVersionRepository(db)
    active = await repo.get_active()
    if active is None:
        raise ModelNotLoadedError("No active model version found.")

    return ModelInfoResponse(
        version_tag=active.version_tag,
        algorithm=active.algorithm,
        is_active=active.is_active,
        trained_at=active.trained_at,
        metrics=active.metrics,
    )
