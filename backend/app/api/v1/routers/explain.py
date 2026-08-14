"""Explanation endpoint — grounded SHAP explanation for an existing prediction."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.prediction_schema import ExplainRequest, ExplanationResponse
from app.services.explanation_service import ExplanationService

router = APIRouter()


@router.post("", response_model=ExplanationResponse)
async def explain_transaction(
    payload: ExplainRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ExplanationResponse:
    service = ExplanationService(db)
    result = await service.explain_transaction(payload.transaction_id)
    await db.commit()
    return ExplanationResponse(**result)
