"""Generates or reuses cached SHAP explanations for predictions to avoid repeated computation."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.fraud_explanation import FraudExplanation
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.model_service import ModelService
from sqlalchemy import select


class ExplanationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.model_service = ModelService(session)

    async def explain_transaction(self, transaction_id: uuid.UUID) -> dict[str, Any]:
        transaction = await self.transaction_repo.get_or_404(transaction_id)
        prediction = await self.prediction_repo.get_by_transaction(transaction_id)
        if prediction is None:
            raise NotFoundError(
                f"No prediction found for transaction {transaction_id}. "
                "Run a prediction before requesting an explanation."
            )

        existing = await self._get_existing_explanation(prediction.id)
        if existing is not None:
            return self._to_response(transaction_id, prediction, existing)

        predictor, _active_model_version = await self.model_service.get_active_predictor()

        raw_row = {
            "Time": transaction.time,
            "Amount": float(transaction.amount),
            **{f"V{i}": getattr(transaction, f"v{i}") for i in range(1, 29)},
        }
        explanation_result = predictor.explain(raw_row)

        fraud_explanation = FraudExplanation(
            prediction_id=prediction.id,
            shap_values=explanation_result["shap_values"],
            top_features=explanation_result["top_features"],
            base_value=explanation_result["base_value"],
            value_space=explanation_result["value_space"],
        )
        self.session.add(fraud_explanation)
        await self.session.flush()

        return self._to_response(transaction_id, prediction, fraud_explanation)

    async def _get_existing_explanation(self, prediction_id: uuid.UUID) -> FraudExplanation | None:
        result = await self.session.execute(
            select(FraudExplanation).where(FraudExplanation.prediction_id == prediction_id)
        )
        return result.scalar_one_or_none()

    def _to_response(self, transaction_id: uuid.UUID, prediction, explanation: FraudExplanation) -> dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "prediction_id": prediction.id,
            "predicted_class": prediction.predicted_class.value,
            "fraud_probability": prediction.fraud_probability,
            "risk_level": prediction.risk_level.value,
            "base_value": explanation.base_value,
            "value_space": explanation.value_space,
            "top_features": explanation.top_features,
            "narrative_summary": explanation.narrative_summary,
        }
