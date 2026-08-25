"""
Embedding provider abstraction.

Mirrors the LLMProvider pattern: business logic (chunking, indexing, RAG
retrieval) depends only on EmbeddingProvider.generate_embedding(), never on
a specific vendor. The embedding dimension is configurable via settings and
validated against the Qdrant collection at collection-creation time.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings
from app.core.logging import logger

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class EmbeddingError(Exception):
    pass


class EmbeddingProvider(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding generation, used by the indexing pipeline to avoid
        sequential round-trips where the provider supports batching."""
        raise NotImplementedError


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
        max_retries: int = 3,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_key = api_key or settings.effective_embedding_api_key
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.max_retries = max_retries
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def generate_embedding(self, text: str) -> list[float]:
        client = await self._get_client()

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(
                    f"{GEMINI_BASE_URL}/{self.model}:embedContent",
                    params={"key": self.api_key},
                    json={
                        "model": f"models/{self.model}",
                        "content": {"parts": [{"text": text}]},
                        "outputDimensionality": self.dimension,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]["values"]
            except httpx.HTTPStatusError as error:
                status_code = error.response.status_code
                if status_code != 429:
                    raise EmbeddingError(str(error)) from error

                if attempt == self.max_retries:
                    logger.error(
                        "Gemini embedding rate limit still exceeded after retries"
                    )
                    raise EmbeddingError("Embedding rate limit exceeded") from error

                delay = 2 * (2**attempt)
                logger.warning(
                    "Gemini embedding rate limited. Retrying in %ds...", delay
                )
                await asyncio.sleep(delay)
            except (httpx.RequestError, KeyError) as error:
                raise EmbeddingError(str(error)) from error

        raise EmbeddingError("Embedding generation failed")

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        # Gemini's embedContent does not support true batching in the same
        # way OpenAI's API does, so we fan out concurrently in small groups
        # to get the benefit of parallelism without overwhelming rate limits.
        results: list[list[float]] = []
        batch_size = 5

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = await asyncio.gather(
                *(self.generate_embedding(text) for text in batch)
            )
            results.extend(batch_results)

        return results
