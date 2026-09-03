"""Stores transaction data and provenance, with V1-V28 as individually queryable ORM fields."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.chat_history import ChatHistory
    from app.models.prediction import Prediction
    from app.models.user import User


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    external_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    time: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)

    # ---- PCA feature columns (V1-V28) ----
    v1: Mapped[float] = mapped_column(Float, nullable=False)
    v2: Mapped[float] = mapped_column(Float, nullable=False)
    v3: Mapped[float] = mapped_column(Float, nullable=False)
    v4: Mapped[float] = mapped_column(Float, nullable=False)
    v5: Mapped[float] = mapped_column(Float, nullable=False)
    v6: Mapped[float] = mapped_column(Float, nullable=False)
    v7: Mapped[float] = mapped_column(Float, nullable=False)
    v8: Mapped[float] = mapped_column(Float, nullable=False)
    v9: Mapped[float] = mapped_column(Float, nullable=False)
    v10: Mapped[float] = mapped_column(Float, nullable=False)
    v11: Mapped[float] = mapped_column(Float, nullable=False)
    v12: Mapped[float] = mapped_column(Float, nullable=False)
    v13: Mapped[float] = mapped_column(Float, nullable=False)
    v14: Mapped[float] = mapped_column(Float, nullable=False)
    v15: Mapped[float] = mapped_column(Float, nullable=False)
    v16: Mapped[float] = mapped_column(Float, nullable=False)
    v17: Mapped[float] = mapped_column(Float, nullable=False)
    v18: Mapped[float] = mapped_column(Float, nullable=False)
    v19: Mapped[float] = mapped_column(Float, nullable=False)
    v20: Mapped[float] = mapped_column(Float, nullable=False)
    v21: Mapped[float] = mapped_column(Float, nullable=False)
    v22: Mapped[float] = mapped_column(Float, nullable=False)
    v23: Mapped[float] = mapped_column(Float, nullable=False)
    v24: Mapped[float] = mapped_column(Float, nullable=False)
    v25: Mapped[float] = mapped_column(Float, nullable=False)
    v26: Mapped[float] = mapped_column(Float, nullable=False)
    v27: Mapped[float] = mapped_column(Float, nullable=False)
    v28: Mapped[float] = mapped_column(Float, nullable=False)

    # ---- Relationships ----
    uploaded_by_user: Mapped["User | None"] = relationship(
        back_populates="uploaded_transactions", foreign_keys=[uploaded_by]
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatHistory"]] = relationship(back_populates="transaction")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Transaction id={self.id} amount={self.amount}>"

    def feature_vector(self) -> list[float]:
        """Returns [V1..V28] in order — used by the ML engine (Phase 6-8)."""
        return [getattr(self, f"v{i}") for i in range(1, 29)]
