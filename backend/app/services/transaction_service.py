"""
TransactionService — read-side queries for transaction history and
detail views. No mutation logic here; transactions are only ever
created via PredictionService (single) or the upload router (batch).
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.transaction_repository import TransactionRepository


def _latest_prediction(transaction) -> Any | None:
    if not transaction.predictions:
        return None
    return max(transaction.predictions, key=lambda p: p.created_at)


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TransactionRepository(session)

    async def list_transactions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        risk_level: str | None = None,
        predicted_class: str | None = None,
        batch_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        transactions, total = await self.repo.list_with_predictions(
            page=page,
            page_size=page_size,
            risk_level=risk_level,
            predicted_class=predicted_class,
            batch_id=batch_id,
        )
        items = [
            {"transaction": txn, "prediction": _latest_prediction(txn)} for txn in transactions
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_transaction_detail(self, transaction_id: uuid.UUID) -> dict[str, Any]:
        transaction = await self.repo.get_with_predictions(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Transaction {transaction_id} not found.")
        return {"transaction": transaction, "prediction": _latest_prediction(transaction)}
