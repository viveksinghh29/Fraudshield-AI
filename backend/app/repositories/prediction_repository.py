"""PredictionRepository — dashboard aggregate queries live here, not in services."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select

from app.models.prediction import Prediction, PredictedClass, RiskLevel
from app.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    model = Prediction

    async def get_by_transaction(self, transaction_id: uuid.UUID) -> Prediction | None:
        result = await self.session.execute(
            select(Prediction)
            .where(Prediction.transaction_id == transaction_id)
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_class(
        self, since: datetime | None = None
    ) -> dict[str, int]:
        """Powers the dashboard's fraud-count / fraud-rate KPI cards."""
        query = select(Prediction.predicted_class, func.count()).group_by(Prediction.predicted_class)
        if since:
            query = query.where(Prediction.created_at >= since)
        result = await self.session.execute(query)
        counts = {row[0].value: row[1] for row in result.all()}
        return {
            "fraud": counts.get(PredictedClass.FRAUD.value, 0),
            "legitimate": counts.get(PredictedClass.LEGITIMATE.value, 0),
        }

    async def risk_distribution(self, since: datetime | None = None) -> dict[str, int]:
        query = select(Prediction.risk_level, func.count()).group_by(Prediction.risk_level)
        if since:
            query = query.where(Prediction.created_at >= since)
        result = await self.session.execute(query)
        counts = {row[0].value: row[1] for row in result.all()}
        return {level.value: counts.get(level.value, 0) for level in RiskLevel}

    async def fraud_trend_by_day(self, *, days: int = 30) -> list[dict[str, Any]]:
        """
        Daily transaction/fraud counts for the trend chart on the
        Analytics page. Uses Postgres's date_trunc rather than pulling
        every row into Python and grouping there -- this scales to
        however many predictions exist without the query result size
        growing with the dataset.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        day_bucket = func.date_trunc("day", Prediction.created_at).label("day")

        query = (
            select(
                day_bucket,
                func.count().label("total"),
                func.sum(case((Prediction.predicted_class == PredictedClass.FRAUD, 1), else_=0)).label(
                    "fraud_count"
                ),
            )
            .where(Prediction.created_at >= since)
            .group_by(day_bucket)
            .order_by(day_bucket)
        )
        result = await self.session.execute(query)
        return [
            {
                "date": row.day.date().isoformat(),
                "total_transactions": int(row.total),
                "fraud_count": int(row.fraud_count),
            }
            for row in result.all()
        ]

    async def average_metrics(self, since: datetime | None = None) -> dict[str, float]:
        """Average fraud probability and average prediction confidence across all predictions."""
        query = select(
            func.avg(Prediction.fraud_probability).label("avg_probability"),
            func.count().label("total"),
        )
        if since:
            query = query.where(Prediction.created_at >= since)
        result = await self.session.execute(query)
        row = result.one()

        avg_probability = float(row.avg_probability) if row.avg_probability is not None else 0.0
        # confidence = distance from the 0.5 decision boundary, rescaled to [0, 1]
        avg_confidence = abs(avg_probability - 0.5) * 2

        return {
            "avg_fraud_probability": round(avg_probability, 4),
            "avg_prediction_confidence": round(avg_confidence, 4),
            "total_predictions": int(row.total),
        }
