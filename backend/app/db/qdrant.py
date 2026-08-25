"""
Qdrant client connection.

Equivalent to the original config/qdrant.js. Collection creation/validation
and vector operations live in app/services/vector/qdrant_service.py -- this
module only owns the client instance and connectivity check.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.core.config import settings
from app.core.logging import logger

_client: AsyncQdrantClient | None = None


async def connect_qdrant() -> None:
    global _client
    try:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        collections = await _client.get_collections()
        logger.info("Qdrant connected. Collections: %d", len(collections.collections))
    except Exception as error:  # noqa: BLE001
        logger.error("Qdrant connection failed: %s", error)
        # Qdrant is required for RAG/indexing but we don't want to crash the
        # whole app at boot (health checks, auth, etc. can still function).
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
        )


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_qdrant_client() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError(
            "Qdrant has not been initialized. Call connect_qdrant() first."
        )
    return _client
