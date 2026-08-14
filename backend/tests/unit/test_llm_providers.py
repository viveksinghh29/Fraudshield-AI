"""
Provider tests using httpx.MockTransport.

This exercises the REAL request-construction and response-parsing code
paths in each provider -- the mock only replaces the actual network
socket, not any of the provider's own logic. This is what actually
verifies "does OllamaProvider build the right JSON body and correctly
extract the reply" rather than assuming it from reading the code.
"""

import httpx
import pytest

from app.core.exceptions import LLMProviderError
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider


def _client_with_transport(transport: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=transport)


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ollama_provider_sends_correct_request_and_parses_response():
    captured_request = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["body"] = httpx.Request.read(request)
        import json

        payload = json.loads(request.content)
        captured_request["payload"] = payload
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "mock reply"}})

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.1", http_client=client)

    reply = await provider.generate(
        system_prompt="SYSTEM CONTEXT HERE",
        messages=[{"role": "user", "content": "Why was this flagged?"}],
    )

    assert reply == "mock reply"
    assert captured_request["url"] == "http://fake-ollama:11434/api/chat"
    assert captured_request["payload"]["model"] == "llama3.1"
    assert captured_request["payload"]["messages"][0] == {
        "role": "system",
        "content": "SYSTEM CONTEXT HERE",
    }
    assert captured_request["payload"]["messages"][1] == {
        "role": "user",
        "content": "Why was this flagged?",
    }
    assert captured_request["payload"]["stream"] is False
    await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_raises_llm_provider_error_on_http_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "internal error"})

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://fake-ollama:11434", http_client=client)

    with pytest.raises(LLMProviderError, match="HTTP 500"):
        await provider.generate(system_prompt="ctx", messages=[{"role": "user", "content": "hi"}])
    await client.aclose()


@pytest.mark.asyncio
async def test_ollama_provider_raises_on_malformed_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://fake-ollama:11434", http_client=client)

    with pytest.raises(LLMProviderError, match="Unexpected Ollama response shape"):
        await provider.generate(system_prompt="ctx", messages=[{"role": "user", "content": "hi"}])
    await client.aclose()


# ---------------------------------------------------------------------------
# GroqProvider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_groq_provider_sends_bearer_auth_and_parses_openai_shape():
    captured_request = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured_request["auth_header"] = request.headers.get("authorization")
        captured_request["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "groq mock reply"}}]},
        )

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = GroqProvider(
        api_key="test-key-123", base_url="http://fake-groq/openai/v1", http_client=client
    )

    reply = await provider.generate(
        system_prompt="ctx", messages=[{"role": "user", "content": "explain this"}]
    )

    assert reply == "groq mock reply"
    assert captured_request["auth_header"] == "Bearer test-key-123"
    assert captured_request["payload"]["messages"][0]["role"] == "system"
    await client.aclose()


@pytest.mark.asyncio
async def test_groq_provider_requires_api_key():
    from app.core.config import get_settings

    settings = get_settings()
    original = settings.GROQ_API_KEY
    settings.GROQ_API_KEY = None
    try:
        with pytest.raises(LLMProviderError, match="GROQ_API_KEY is not configured"):
            GroqProvider(api_key=None)
    finally:
        settings.GROQ_API_KEY = original


@pytest.mark.asyncio
async def test_groq_provider_raises_on_auth_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid api key"})

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = GroqProvider(api_key="bad-key", base_url="http://fake-groq/openai/v1", http_client=client)

    with pytest.raises(LLMProviderError, match="HTTP 401"):
        await provider.generate(system_prompt="ctx", messages=[{"role": "user", "content": "hi"}])
    await client.aclose()


# ---------------------------------------------------------------------------
# OpenAICompatibleProvider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_compatible_provider_sends_correct_request():
    captured_request = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured_request["url"] = str(request.url)
        captured_request["payload"] = json.loads(request.content)
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "vllm mock reply"}}]}
        )

    client = _client_with_transport(httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        base_url="http://localhost:8000/v1", model="mistral-7b", api_key="local-key", http_client=client
    )

    reply = await provider.generate(system_prompt="ctx", messages=[{"role": "user", "content": "hi"}])

    assert reply == "vllm mock reply"
    assert captured_request["url"] == "http://localhost:8000/v1/chat/completions"
    assert captured_request["payload"]["model"] == "mistral-7b"
    await client.aclose()


def test_openai_compatible_provider_requires_base_url():
    from app.core.config import get_settings

    settings = get_settings()
    original = settings.OPENAI_COMPATIBLE_BASE_URL
    settings.OPENAI_COMPATIBLE_BASE_URL = None
    try:
        with pytest.raises(LLMProviderError, match="OPENAI_COMPATIBLE_BASE_URL is not configured"):
            OpenAICompatibleProvider(base_url=None)
    finally:
        settings.OPENAI_COMPATIBLE_BASE_URL = original


@pytest.mark.asyncio
async def test_openai_compatible_provider_requires_model():
    with pytest.raises(LLMProviderError, match="OPENAI_COMPATIBLE_MODEL is not configured"):
        OpenAICompatibleProvider(base_url="http://localhost:8000/v1", model=None, api_key="k")
