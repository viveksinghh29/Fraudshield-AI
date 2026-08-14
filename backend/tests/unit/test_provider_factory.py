"""
Unit tests for app.llm.provider_factory.get_llm_provider().

Mutates the cached Settings singleton's attributes directly rather
than reloading modules -- get_settings() is @lru_cache'd, so every
module that did `settings = get_settings()` at import time holds a
reference to the exact same object; mutating its attributes propagates
everywhere instantly. Tried importlib.reload() first, but that creates
new class objects distinct from what this test file already imported,
which breaks isinstance() checks in a confusing way (an object that IS
an OpenAICompatibleProvider fails isinstance() against a stale class
reference) -- direct attribute mutation avoids that pitfall entirely.
"""

import pytest

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.llm.provider_factory import get_llm_provider


@pytest.fixture
def settings():
    s = get_settings()
    original = {
        "LLM_PROVIDER": s.LLM_PROVIDER,
        "GROQ_API_KEY": s.GROQ_API_KEY,
        "OPENAI_COMPATIBLE_BASE_URL": s.OPENAI_COMPATIBLE_BASE_URL,
        "OPENAI_COMPATIBLE_MODEL": s.OPENAI_COMPATIBLE_MODEL,
    }
    yield s
    for key, value in original.items():
        setattr(s, key, value)


def test_get_llm_provider_returns_ollama_provider(settings):
    settings.LLM_PROVIDER = "ollama"
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)


def test_get_llm_provider_returns_groq_provider(settings):
    settings.LLM_PROVIDER = "groq"
    settings.GROQ_API_KEY = "test-key"
    provider = get_llm_provider()
    assert isinstance(provider, GroqProvider)


def test_get_llm_provider_returns_openai_compatible_provider(settings):
    settings.LLM_PROVIDER = "openai_compatible"
    settings.OPENAI_COMPATIBLE_BASE_URL = "http://localhost:8000/v1"
    settings.OPENAI_COMPATIBLE_MODEL = "test-model"
    provider = get_llm_provider()
    assert isinstance(provider, OpenAICompatibleProvider)


def test_get_llm_provider_propagates_groq_config_error_when_api_key_missing(settings):
    settings.LLM_PROVIDER = "groq"
    settings.GROQ_API_KEY = None
    with pytest.raises(LLMProviderError, match="GROQ_API_KEY is not configured"):
        get_llm_provider()


def test_invalid_llm_provider_rejected_at_settings_level(monkeypatch):
    """
    LLM_PROVIDER is a Pydantic Literal["ollama", "groq", "openai_compatible"],
    so an invalid value is actually rejected here, at Settings construction --
    not inside get_llm_provider()'s own `raise ValueError` branch, which
    is unreachable in practice as a result (kept as defensive code, but
    this test verifies where the real validation boundary is).
    """
    from pydantic import ValidationError

    monkeypatch.setenv("LLM_PROVIDER", "not_a_real_provider")

    from app.core.config import Settings

    with pytest.raises(ValidationError, match="LLM_PROVIDER"):
        Settings()
