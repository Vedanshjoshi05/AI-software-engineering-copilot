"""Factory that resolves the configured LLM provider without coupling
callers to a specific vendor class."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.llm_provider import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        return GeminiProvider()

    # Future providers (OpenAI, OpenRouter, local models) can be added here
    # without touching any business logic that depends on LLMProvider.
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
