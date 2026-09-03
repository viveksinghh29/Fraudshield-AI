"""
Prediction model — one row per model inference run against a transaction.
"""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.fraud_explanation import FraudExplanation
    from app.models.model_version import ModelVersion
    from app.models.transaction import Transaction


class PredictedClass(str, enum.Enum):
    FRAUD = "fraud"
    LEGITIMATE = "legitimate"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Prediction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "predictions"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False
    )
    predicted_class: Mapped[PredictedClass] = mapped_column(
        Enum(PredictedClass, name="predicted_class", native_enum=True), nullable=False
    )
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level", native_enum=True), nullable=False, index=True
    )

    # ---- Relationships ----
    transaction: Mapped["Transaction"] = relationship(back_populates="predictions")
    model_version: Mapped["ModelVersion"] = relationship(back_populates="predictions")
    explanation: Mapped["FraudExplanation | None"] = relationship(
        back_populates="prediction", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Prediction id={self.id} class={self.predicted_class} "
            f"prob={self.fraud_probability:.4f} risk={self.risk_level}>"
        )
