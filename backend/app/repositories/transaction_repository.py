"""TransactionRepository — batch lookups and bulk insert for CSV uploads."""

import uuid
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    async def get_by_batch(self, batch_id: uuid.UUID) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.batch_id == batch_id)
        )
        return list(result.scalars().all())

    async def get_with_predictions(self, transaction_id: uuid.UUID) -> Transaction | None:
        """Fetches one transaction with its predictions eagerly loaded (avoids a second round trip)."""
        result = await self.session.execute(
            select(Transaction)
            .options(selectinload(Transaction.predictions))
            .where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_with_predictions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        risk_level: str | None = None,
        predicted_class: str | None = None,
        batch_id: uuid.UUID | None = None,
    ) -> tuple[list[Transaction], int]:
        """
        Paginated transaction list, each with its predictions eagerly
        loaded via selectinload (one extra query total, not one per
        row). Optional filters join through to the latest prediction
        per transaction, applied in Python since a transaction may
        have more than one prediction (e.g. re-scored after a model
        update) and "latest" isn't expressible as a simple WHERE clause
        without a window function -- acceptable at this data scale.
        """
        from app.models.prediction import Prediction

        query = select(Transaction).options(selectinload(Transaction.predictions))
        count_query = select(func.count()).select_from(Transaction)

        if batch_id is not None:
            query = query.where(Transaction.batch_id == batch_id)
            count_query = count_query.where(Transaction.batch_id == batch_id)

        if risk_level is not None or predicted_class is not None:
            query = query.join(Prediction, Prediction.transaction_id == Transaction.id)
            count_query = count_query.join(Prediction, Prediction.transaction_id == Transaction.id)
            if risk_level is not None:
                query = query.where(Prediction.risk_level == risk_level)
                count_query = count_query.where(Prediction.risk_level == risk_level)
            if predicted_class is not None:
                query = query.where(Prediction.predicted_class == predicted_class)
                count_query = count_query.where(Prediction.predicted_class == predicted_class)

        query = query.order_by(desc(Transaction.created_at)).offset((page - 1) * page_size).limit(page_size)

        total = (await self.session.execute(count_query)).scalar_one()
        items = (await self.session.execute(query)).scalars().unique().all()
        return list(items), total

    async def bulk_create(self, rows: list[dict[str, Any]]) -> list[Transaction]:
        """
        Used by the CSV upload / batch prediction flow (Phase 8) to insert
        many transactions in one round trip instead of one `create()` per row.
        """
        instances = [Transaction(**row) for row in rows]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances
