"""
FraudExplanation model — one-to-one with Prediction.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.prediction import Prediction


class FraudExplanation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fraud_explanations"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # enforces the one-to-one relationship at the DB level
    )
    shap_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    top_features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    base_value: Mapped[float] = mapped_column(Float, nullable=False)
    value_space: Mapped[str] = mapped_column(String(16), nullable=False, default="probability")
    narrative_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- Relationships ----
    prediction: Mapped["Prediction"] = relationship(back_populates="explanation")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FraudExplanation id={self.id} prediction_id={self.prediction_id}>"
