"""
ModelVersion model — the model registry.

Exactly one row should have `is_active=True` at any time; this is
enforced at the service layer (Phase 7's `ModelService.activate()`
deactivates the previous active row inside the same transaction)
rather than a DB constraint, since some databases make a true
"at most one True" constraint awkward without a partial unique index.
A partial unique index is added in the migration for defense in depth.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.prediction import Prediction


class ModelVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_versions"

    version_tag: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ---- Relationships ----
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model_version")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ModelVersion id={self.id} tag={self.version_tag} active={self.is_active}>"
