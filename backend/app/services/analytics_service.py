"""
AnalyticsService — aggregate KPIs for the dashboard and deeper
analytics (fraud trend, risk distribution, confidence stats).

All aggregation happens in the repository layer via SQL (COUNT, AVG,
GROUP BY) rather than pulling every row into Python -- this keeps the
dashboard fast regardless of how many predictions have accumulated.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.model_repo = ModelVersionRepository(session)

    async def get_dashboard(self, *, recent_limit: int = 10) -> dict[str, Any]:
        class_counts = await self.prediction_repo.count_by_class()
        risk_distribution = await self.prediction_repo.risk_distribution()

        total_transactions = class_counts["fraud"] + class_counts["legitimate"]
        fraud_rate_pct = (
            round(100 * class_counts["fraud"] / total_transactions, 4) if total_transactions else 0.0
        )

        recent_transactions, _ = await self.transaction_repo.list_with_predictions(
            page=1, page_size=recent_limit
        )

        active_model = await self.model_repo.get_active()

        return {
            "total_transactions": total_transactions,
            "fraud_count": class_counts["fraud"],
            "legitimate_count": class_counts["legitimate"],
            "fraud_rate_pct": fraud_rate_pct,
            "risk_distribution": risk_distribution,
            "recent_transactions": recent_transactions,
            "active_model_version": active_model.version_tag if active_model else None,
            "active_model_algorithm": active_model.algorithm if active_model else None,
        }

    async def get_analytics(self, *, days: int = 30) -> dict[str, Any]:
        fraud_trend = await self.prediction_repo.fraud_trend_by_day(days=days)
        risk_distribution = await self.prediction_repo.risk_distribution()
        averages = await self.prediction_repo.average_metrics()

        return {
            "fraud_trend": fraud_trend,
            "risk_distribution": risk_distribution,
            **averages,
        }
