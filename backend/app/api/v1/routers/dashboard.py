"""Dashboard endpoint — top-level KPI cards for the analyst console home screen."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction_schema import DashboardResponse, PredictionSummary, TransactionSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    service = AnalyticsService(db)
    result = await service.get_dashboard()

    recent = []
    for txn in result["recent_transactions"]:
        prediction = max(txn.predictions, key=lambda p: p.created_at) if txn.predictions else None
        recent.append(
            TransactionSummary(
                id=txn.id,
                time=txn.time,
                amount=float(txn.amount),
                batch_id=txn.batch_id,
                created_at=txn.created_at,
                prediction=(
                    PredictionSummary(
                        id=prediction.id,
                        predicted_class=prediction.predicted_class.value,
                        fraud_probability=prediction.fraud_probability,
                        risk_level=prediction.risk_level.value,
                        created_at=prediction.created_at,
                    )
                    if prediction
                    else None
                ),
            )
        )

    return DashboardResponse(
        total_transactions=result["total_transactions"],
        fraud_count=result["fraud_count"],
        legitimate_count=result["legitimate_count"],
        fraud_rate_pct=result["fraud_rate_pct"],
        risk_distribution=result["risk_distribution"],
        recent_predictions=recent,
        active_model_version=result["active_model_version"],
        active_model_algorithm=result["active_model_algorithm"],
    )
