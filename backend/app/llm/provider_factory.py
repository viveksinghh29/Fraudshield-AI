"""
Provider factory — reads LLM_PROVIDER from settings and returns the
matching provider instance. This is the one place that switches on
provider choice; everything else in the app depends on the LLMProvider
interface only, so adding a fourth provider later means adding one
branch here and nothing else.
"""

from app.core.config import get_settings
from app.llm.base_provider import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider

settings = get_settings()


def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER

    if provider == "ollama":
        return OllamaProvider()
    if provider == "groq":
        return GroqProvider()
    if provider == "openai_compatible":
        return OpenAICompatibleProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}'. Expected one of: ollama, groq, openai_compatible."
    )
