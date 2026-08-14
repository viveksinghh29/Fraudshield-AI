"""
ChatAssistantService — orchestrates a single chat turn: sanitize
input, build grounded context (if a transaction is referenced),
call the active LLM provider, persist both sides of the turn, and
return the response with the grounding metadata attached.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.llm.base_provider import LLMProvider
from app.llm.context_builder import build_transaction_context, render_context_as_text
from app.llm.guardrails import check_response_grounding, sanitize_user_input
from app.llm.prompt_templates import NO_TRANSACTION_SYSTEM_PROMPT, build_system_prompt
from app.models.chat_history import ChatRole
from app.repositories.chat_repository import ChatRepository
from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.explanation_service import ExplanationService

CHAT_HISTORY_TURN_LIMIT = 20


class ChatAssistantService:
    def __init__(self, session: AsyncSession, llm_provider: LLMProvider) -> None:
        self.session = session
        self.llm_provider = llm_provider
        self.chat_repo = ChatRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.model_version_repo = ModelVersionRepository(session)
        self.explanation_service = ExplanationService(session)

    async def handle_turn(
        self,
        *,
        user_id: uuid.UUID,
        user_message: str,
        transaction_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        sanitized_message = sanitize_user_input(user_message)

        context_snapshot: dict[str, Any] | None = None
        if transaction_id is not None:
            system_prompt, context_snapshot = await self._build_grounded_system_prompt(transaction_id)
        else:
            system_prompt = NO_TRANSACTION_SYSTEM_PROMPT

        history = await self.chat_repo.get_thread(
            user_id=user_id, transaction_id=transaction_id, limit=CHAT_HISTORY_TURN_LIMIT
        )
        conversation = [{"role": turn.role.value, "content": turn.message} for turn in history]
        conversation.append({"role": "user", "content": sanitized_message})

        assistant_reply = await self.llm_provider.generate(
            system_prompt=system_prompt, messages=conversation
        )

        known_features = (
            [f["feature"] for f in context_snapshot["explanation"]["top_contributing_features"]]
            if context_snapshot
            else []
        )
        grounding_check = check_response_grounding(assistant_reply, known_features)

        await self.chat_repo.create(
            user_id=user_id,
            transaction_id=transaction_id,
            role=ChatRole.USER,
            message=sanitized_message,
            context_snapshot=None,
        )
        await self.chat_repo.create(
            user_id=user_id,
            transaction_id=transaction_id,
            role=ChatRole.ASSISTANT,
            message=assistant_reply,
            context_snapshot=context_snapshot,
        )

        return {
            "message": assistant_reply,
            "grounded": context_snapshot is not None,
            "context_used": context_snapshot,
            "grounding_check": grounding_check,
        }

    async def _build_grounded_system_prompt(
        self, transaction_id: uuid.UUID
    ) -> tuple[str, dict[str, Any]]:
        transaction = await self.transaction_repo.get_or_404(transaction_id)
        prediction = await self.prediction_repo.get_by_transaction(transaction_id)
        if prediction is None:
            raise NotFoundError(
                f"No prediction found for transaction {transaction_id}. "
                "Run a prediction before asking the assistant about it."
            )

        model_version = await self.model_version_repo.get_or_404(prediction.model_version_id)
        explanation_result = await self.explanation_service.explain_transaction(transaction_id)

        context = build_transaction_context(
            transaction_id=str(transaction.id),
            transaction_time=transaction.time,
            transaction_amount=float(transaction.amount),
            predicted_class=prediction.predicted_class.value,
            fraud_probability=prediction.fraud_probability,
            risk_level=prediction.risk_level.value,
            model_version=model_version.version_tag,
            top_features=explanation_result["top_features"],
            base_value=explanation_result["base_value"],
            value_space=explanation_result["value_space"],
        )

        context_block = render_context_as_text(context)
        system_prompt = build_system_prompt(context_block)
        return system_prompt, context
