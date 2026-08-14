"""
Ollama provider — local/offline LLM via Ollama's /api/chat endpoint.

httpx is used directly rather than a client library so the base URL
is trivially overridable (constructor arg), which matters for testing
against a local mock server as well as for pointing at a
non-default Ollama installation.
"""

import httpx

from app.core.config import get_settings
from app.llm.base_provider import LLMProvider, LLMProviderError

settings = get_settings()


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout
        # Injectable for tests (httpx.AsyncClient(transport=httpx.MockTransport(...)));
        # defaults to a real client hitting the network otherwise.
        self._http_client = http_client

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": False,
            "options": {"temperature": settings.LLM_TEMPERATURE},
        }

        try:
            if self._http_client is not None:
                response = await self._http_client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    response.raise_for_status()
                    data = response.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Could not reach Ollama at {self.base_url}: {exc}") from exc

        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMProviderError(f"Unexpected Ollama response shape: {data}") from exc
