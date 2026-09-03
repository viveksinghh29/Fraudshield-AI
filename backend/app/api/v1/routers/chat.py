"""Analyst AI Assistant chat endpoint.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.llm.base_provider import LLMProvider
from app.llm.provider_factory import get_llm_provider
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat_schema import ChatHistoryResponse, ChatHistoryTurn, ChatRequest, ChatResponse
from app.services.chat_assistant_service import ChatAssistantService

router = APIRouter()


def get_llm_provider_dependency() -> LLMProvider:
    return get_llm_provider()


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: LLMProvider = Depends(get_llm_provider_dependency),
) -> ChatResponse:
    service = ChatAssistantService(db, provider)

    result = await service.handle_turn(
        user_id=current_user.id,
        user_message=payload.message,
        transaction_id=payload.transaction_id,
    )
    await db.commit()

    return ChatResponse(
        message=result["message"],
        grounded=result["grounded"],
        context_used=result["context_used"],
    )


@router.get("/history/{transaction_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    repo = ChatRepository(db)
    turns = await repo.get_thread(user_id=current_user.id, transaction_id=transaction_id, limit=100)

    return ChatHistoryResponse(
        transaction_id=transaction_id,
        turns=[
            ChatHistoryTurn(role=turn.role.value, message=turn.message, created_at=turn.created_at)
            for turn in turns
        ],
    )
