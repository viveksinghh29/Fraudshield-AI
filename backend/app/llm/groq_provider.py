"""
Groq provider — Groq's OpenAI-compatible /chat/completions endpoint.

Implemented directly with httpx (same pattern as OllamaProvider)
rather than the groq SDK, so all three providers share one consistent
request/response handling style and the endpoint is overridable for
testing without needing to fight the SDK's own client configuration.
"""

import httpx

from app.core.config import get_settings
from app.llm.base_provider import LLMProvider, LLMProviderError

settings = get_settings()

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        http_client=None,
    ) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise LLMProviderError(
                "GROQ_API_KEY is not configured. Set it in the environment to use LLM_PROVIDER=groq."
            )
        self.base_url = (base_url or DEFAULT_GROQ_BASE_URL).rstrip("/")
        self.model = model or settings.GROQ_MODEL
        self.timeout = timeout
        self._http_client = http_client

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

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
                f"Groq returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Could not reach Groq at {self.base_url}: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"Unexpected Groq response shape: {data}") from exc
