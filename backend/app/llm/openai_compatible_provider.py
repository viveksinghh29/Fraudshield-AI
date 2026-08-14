"""
OpenAI-compatible provider — for any endpoint implementing the
OpenAI /chat/completions contract (vLLM, LM Studio, Azure OpenAI's
compatible mode, self-hosted gateways, etc). Structurally identical
to GroqProvider (Groq itself is exactly this contract), kept as a
separate class because its configuration (base_url, api_key, model)
is fully user-supplied rather than defaulting to one known vendor.
"""

import httpx

from app.core.config import get_settings
from app.llm.base_provider import LLMProvider, LLMProviderError

settings = get_settings()


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        http_client=None,
    ) -> None:
        self.base_url = (base_url or settings.OPENAI_COMPATIBLE_BASE_URL or "").rstrip("/")
        if not self.base_url:
            raise LLMProviderError(
                "OPENAI_COMPATIBLE_BASE_URL is not configured. Set it in the environment "
                "to use LLM_PROVIDER=openai_compatible."
            )
        self.api_key = api_key or settings.OPENAI_COMPATIBLE_API_KEY
        self.model = model or settings.OPENAI_COMPATIBLE_MODEL
        if not self.model:
            raise LLMProviderError(
                "OPENAI_COMPATIBLE_MODEL is not configured. Set it in the environment "
                "to use LLM_PROVIDER=openai_compatible."
            )
        self.timeout = timeout
        self._http_client = http_client

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            if self._http_client is not None:
                response = await self._http_client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions", json=payload, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"OpenAI-compatible endpoint returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:300]}"
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Could not reach {self.base_url}: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"Unexpected response shape: {data}") from exc
