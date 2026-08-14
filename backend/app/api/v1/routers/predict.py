"""
Prediction endpoints: single transaction prediction, and triggering
batch prediction over an already-uploaded batch (see
POST /transactions/upload for the upload step itself).
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.prediction_schema import (
    BatchStatusResponse,
    BatchUploadResponse,
    PredictionResponse,
    TransactionInput,
)
from app.services.prediction_service import PredictionService
from app.tasks.batch_prediction_task import predict_batch_task

router = APIRouter()


@router.post("", response_model=PredictionResponse)
async def predict_single(
    payload: TransactionInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PredictionResponse:
    service = PredictionService(db)
    result = await service.predict_single(payload, user_id=current_user.id)
    await db.commit()

    return PredictionResponse(
        transaction_id=result["transaction_id"],
        predicted_class=result["predicted_class"],
        fraud_probability=result["fraud_probability"],
        risk_level=result["risk_level"],
        model_version=result["model_version"],
        threshold_used=result["threshold_used"],
    )


@router.post("/batch", response_model=BatchUploadResponse)
async def trigger_batch_prediction(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchUploadResponse:
    """
    Enqueues a Celery task to predict every transaction already
    uploaded under `batch_id` (see POST /transactions/upload). Returns
    immediately with a task id; poll GET /predict/batch/{batch_id}/status
    for progress.
    """
    repo = TransactionRepository(db)
    transactions = await repo.get_by_batch(batch_id)
    if not transactions:
        raise NotFoundError(f"No transactions found for batch_id={batch_id}. Upload a CSV first.")

    task = predict_batch_task.delay(str(batch_id))

    return BatchUploadResponse(
        batch_id=batch_id,
        transaction_count=len(transactions),
        task_id=task.id,
        status="queued",
    )


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> BatchStatusResponse:
    """
    Progress is derived directly from the data (predictions that exist
    for this batch's transactions vs. total transactions in the batch)
    rather than a separate job-tracking table -- one less thing that
    can drift out of sync with reality.
    """
    total_result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.batch_id == batch_id)
    )
    total = total_result.scalar_one()

    if total == 0:
        raise NotFoundError(f"No transactions found for batch_id={batch_id}.")

    processed_result = await db.execute(
        select(func.count())
        .select_from(Prediction)
        .join(Transaction, Prediction.transaction_id == Transaction.id)
        .where(Transaction.batch_id == batch_id)
    )
    processed = processed_result.scalar_one()

    fraud_result = await db.execute(
        select(func.count())
        .select_from(Prediction)
        .join(Transaction, Prediction.transaction_id == Transaction.id)
        .where(Transaction.batch_id == batch_id, Prediction.predicted_class == "fraud")
    )
    fraud_count = fraud_result.scalar_one()

    status = "completed" if processed == total else ("processing" if processed > 0 else "queued")

    return BatchStatusResponse(
        batch_id=batch_id,
        status=status,
        total_transactions=total,
        processed_transactions=processed,
        fraud_count=fraud_count if processed > 0 else None,
    )
