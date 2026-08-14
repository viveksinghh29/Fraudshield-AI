"""ChatRepository — retrieves ordered chat threads for the Analyst AI Assistant."""

import uuid

from sqlalchemy import select

from app.models.chat_history import ChatHistory
from app.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository[ChatHistory]):
    model = ChatHistory

    async def get_thread(
        self, *, user_id: uuid.UUID, transaction_id: uuid.UUID | None = None, limit: int = 50
    ) -> list[ChatHistory]:
        """
        Returns the most recent `limit` turns, oldest-first, so they can be
        fed straight into the LLM provider as conversation history.
        """
        query = select(ChatHistory).where(ChatHistory.user_id == user_id)
        if transaction_id is not None:
            query = query.where(ChatHistory.transaction_id == transaction_id)
        query = query.order_by(ChatHistory.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        turns = list(result.scalars().all())
        return list(reversed(turns))
