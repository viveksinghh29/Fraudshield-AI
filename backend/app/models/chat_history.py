"""
ChatHistory model — one row per turn in the Analyst AI Assistant chat.
"""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole, name="chat_role", native_enum=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ---- Relationships ----
    user: Mapped["User"] = relationship(back_populates="chat_messages")
    transaction: Mapped["Transaction | None"] = relationship(back_populates="chat_messages")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatHistory id={self.id} role={self.role} user_id={self.user_id}>"
