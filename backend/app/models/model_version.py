"""
ModelVersion model — the model registry.
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
