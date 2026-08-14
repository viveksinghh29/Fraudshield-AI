"""Pydantic v2 schemas for the Analyst AI Assistant chat endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    transaction_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    message: str
    grounded: bool
    context_used: dict[str, Any] | None = None


class ChatHistoryTurn(BaseModel):
    role: str
    message: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    transaction_id: uuid.UUID | None
    turns: list[ChatHistoryTurn]
