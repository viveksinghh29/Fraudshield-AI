"""
PredictionService — orchestrates a single transaction prediction:
persist the transaction, run inference via the active model
(ModelService), persist the prediction, audit-log the event.

Business logic lives here, not in the router (predict.py), per the
Clean Architecture rules from Phase 1.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictedClass, RiskLevel
from app.repositories.audit_repository import AuditRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.prediction_schema import TransactionInput
from app.services.model_service import ModelService


class PredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.audit_repo = AuditRepository(session)
        self.model_service = ModelService(session)

    async def predict_single(
        self, transaction_input: TransactionInput, *, user_id: uuid.UUID | None = None
    ) -> dict[str, Any]:
        predictor, active_model_version = await self.model_service.get_active_predictor()

        raw_row = transaction_input.to_raw_dict()
        result = predictor.predict(raw_row)

        # raw_row uses the Kaggle-schema casing the Predictor expects
        # (Time, Amount, V1..V28); the Transaction ORM model's columns
        # are lowercase (time, amount, v1..v28) -- these must not be
        # conflated, so build the ORM kwargs explicitly rather than
        # passing raw_row straight through.
        transaction_kwargs = {"time": raw_row["Time"], "amount": raw_row["Amount"]}
        for i in range(1, 29):
            transaction_kwargs[f"v{i}"] = raw_row[f"V{i}"]
        transaction = await self.transaction_repo.create(**transaction_kwargs)

        prediction = await self.prediction_repo.create(
            transaction_id=transaction.id,
            model_version_id=active_model_version.id,
            predicted_class=PredictedClass(result["predicted_class"]),
            fraud_probability=result["fraud_probability"],
            risk_level=RiskLevel(result["risk_level"]),
        )

        await self.audit_repo.log(
            action="PREDICTION_CREATED",
            user_id=user_id,
            resource_type="prediction",
            resource_id=prediction.id,
            metadata={
                "transaction_id": str(transaction.id),
                "predicted_class": result["predicted_class"],
                "risk_level": result["risk_level"],
            },
        )

        return {
            "transaction_id": transaction.id,
            "prediction_id": prediction.id,
            "predicted_class": result["predicted_class"],
            "fraud_probability": result["fraud_probability"],
            "risk_level": result["risk_level"],
            "model_version": active_model_version.version_tag,
            "threshold_used": result["threshold_used"],
        }
