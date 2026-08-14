"""Analytics endpoint — fraud trend over time, risk distribution, confidence stats."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction_schema import AnalyticsResponse, FraudTrendPoint
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AnalyticsResponse:
    service = AnalyticsService(db)
    result = await service.get_analytics(days=days)

    return AnalyticsResponse(
        fraud_trend=[FraudTrendPoint(**point) for point in result["fraud_trend"]],
        risk_distribution=result["risk_distribution"],
        avg_fraud_probability=result["avg_fraud_probability"],
        avg_prediction_confidence=result["avg_prediction_confidence"],
        total_predictions=result["total_predictions"],
    )
