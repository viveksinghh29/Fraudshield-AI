"""
LLMProvider — the interface every LLM backend implements.
"""

from abc import ABC, abstractmethod

from app.core.exceptions import LLMProviderError

__all__ = ["LLMProvider", "LLMProviderError"]


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> str:
        """
        Args:
            system_prompt: the grounding instructions + structured
                context (prediction, SHAP values, transaction data).
            messages: conversation history as [{"role": "user"|"assistant", "content": str}, ...],
                oldest first, NOT including the system prompt itself.

        Returns: the assistant's plain-text reply.

        Raises: LLMProviderError on any failure -- callers never need
            to know whether that was a timeout, an API error, or a
            malformed response; it's all "the provider failed".
        """
        raise NotImplementedError
