"""Celery task for batch prediction, bridging synchronous workers with the app's async database layer."""

import asyncio
import uuid

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.prediction import PredictedClass, RiskLevel
from app.repositories.audit_repository import AuditRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.model_service import ModelService
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="predict_batch_task", bind=True, max_retries=2)
def predict_batch_task(self, batch_id: str) -> dict:
    """
    Entry point Celery calls. Delegates to an async implementation so
    the same repositories/services used by the synchronous API routes
    are reused here too, rather than duplicating query logic.

    In production, a Celery worker process has no event loop already
    running, so asyncio.run() works directly. Celery's "eager" testing
    mode (task_always_eager=True) instead executes the task inline,
    synchronously, inside whatever process called .delay() -- which,
    for an async FastAPI route, means a loop is already running, and
    asyncio.run() raises "cannot be called from a running event loop".
    Detected exactly this way while adding API-level tests for the
    batch endpoints. Falls back to running the coroutine in a fresh
    thread (with its own new loop) only in that situation, so both the
    real worker path and the eager-mode test path work correctly.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No loop running in this thread -- the normal Celery worker case.
        return asyncio.run(_predict_batch_async(uuid.UUID(batch_id)))

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _predict_batch_async(uuid.UUID(batch_id)))
        return future.result()


async def _predict_batch_async(batch_id: uuid.UUID) -> dict:
    async with AsyncSessionLocal() as session:
        transaction_repo = TransactionRepository(session)
        prediction_repo = PredictionRepository(session)
        audit_repo = AuditRepository(session)
        model_service = ModelService(session)

        transactions = await transaction_repo.get_by_batch(batch_id)
        if not transactions:
            logger.warning("Batch prediction task found no transactions for batch_id=%s", batch_id)
            return {"batch_id": str(batch_id), "processed": 0, "fraud_count": 0}

        predictor, active_model_version = await model_service.get_active_predictor()

        raw_rows = [
            {
                "Time": txn.time,
                "Amount": float(txn.amount),
                **{f"V{i}": getattr(txn, f"v{i}") for i in range(1, 29)},
            }
            for txn in transactions
        ]
        results = predictor.predict_batch(raw_rows)

        fraud_count = 0
        for transaction, result in zip(transactions, results):
            await prediction_repo.create(
                transaction_id=transaction.id,
                model_version_id=active_model_version.id,
                predicted_class=PredictedClass(result["predicted_class"]),
                fraud_probability=result["fraud_probability"],
                risk_level=RiskLevel(result["risk_level"]),
            )
            if result["predicted_class"] == "fraud":
                fraud_count += 1

        await audit_repo.log(
            action="BATCH_PREDICTION_COMPLETED",
            resource_type="batch",
            resource_id=batch_id,
            metadata={
                "transaction_count": len(transactions),
                "fraud_count": fraud_count,
                "model_version": active_model_version.version_tag,
            },
        )
        await session.commit()

        logger.info(
            "Batch prediction complete for batch_id=%s: %d transactions, %d fraud",
            batch_id,
            len(transactions),
            fraud_count,
        )

        return {
            "batch_id": str(batch_id),
            "processed": len(transactions),
            "fraud_count": fraud_count,
        }
