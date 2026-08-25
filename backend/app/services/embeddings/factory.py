"""Factory that resolves the configured embedding provider."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.embeddings.provider import EmbeddingProvider, GeminiEmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        return GeminiEmbeddingProvider()

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
