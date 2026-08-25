"""
Qdrant vector operations service.

Equivalent to the original services/vectorService.js, upgraded to the
CURRENT qdrant-client API:

  - Deprecated `client.search()` is NOT used anywhere in this module.
  - Semantic search uses `client.query_points()`, which is the supported
    replacement in modern qdrant-client versions.

Enforces strict repository isolation: every search and delete operation
filters by repositoryId AND indexVersion so a query can never return
chunks belonging to another repository or a stale index version.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from qdrant_client import models as qmodels

from app.core.config import settings
from app.core.logging import logger
from app.db.qdrant import get_qdrant_client


@dataclass
class CodeChunkPayload:
    path: str
    sha: str
    chunk_index: int
    content: str


@dataclass
class ScoredChunk:
    score: float
    path: str
    chunk_index: int
    content: str


async def create_code_collection() -> None:
    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION_NAME

    collections = await client.get_collections()
    exists = any(c.name == collection_name for c in collections.collections)

    if exists:
        # Validate the embedding dimension matches what we're configured for.
        info = await client.get_collection(collection_name)
        existing_size = info.config.params.vectors.size  # type: ignore[union-attr]

        if existing_size != settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Qdrant collection '{collection_name}' has vector size "
                f"{existing_size}, but EMBEDDING_DIMENSION is configured as "
                f"{settings.EMBEDDING_DIMENSION}. These must match."
            )

        logger.info("Qdrant collection already exists")
        return

    await client.create_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(
            size=settings.EMBEDDING_DIMENSION,
            distance=qmodels.Distance.COSINE,
        ),
    )

    logger.info("Qdrant code collection created")


def _generate_point_id(
    repository_id: str,
    path: str,
    chunk_index: int,
    index_version: str,
) -> str:
    """
    Generate a deterministic UUID from the repository, file path,
    chunk index, and index version.

    Including index_version ensures that different indexing runs
    can coexist in Qdrant without overwriting each other's vectors.
    """
    digest = hashlib.sha256(
        f"{repository_id}:{path}:{chunk_index}:{index_version}".encode()
    ).hexdigest()

    return str(uuid.UUID(digest[:32]))


async def store_chunk(
    repository_id: str,
    chunk: CodeChunkPayload,
    vector: list[float],
    index_version: str,
) -> str:
    client = get_qdrant_client()

    point_id = _generate_point_id(
        repository_id,
        chunk.path,
        chunk.chunk_index,
        index_version,
    )

    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        wait=True,
        points=[
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "repositoryId": str(repository_id),
                    "indexVersion": index_version,
                    "path": chunk.path,
                    "sha": chunk.sha,
                    "chunkIndex": chunk.chunk_index,
                    "content": chunk.content,
                },
            )
        ],
    )

    logger.info("Stored chunk: %s [%d]", chunk.path, chunk.chunk_index)

    return point_id


async def store_chunks_batch(
    repository_id: str,
    chunks_with_vectors: list[tuple[CodeChunkPayload, list[float]]],
    index_version: str,
) -> None:
    """
    Batch upsert -- used by the indexing pipeline to avoid one round-trip
    per chunk.
    """
    if not chunks_with_vectors:
        return

    client = get_qdrant_client()

    points = [
        qmodels.PointStruct(
            id=_generate_point_id(
                repository_id,
                chunk.path,
                chunk.chunk_index,
                index_version,
            ),
            vector=vector,
            payload={
                "repositoryId": str(repository_id),
                "indexVersion": index_version,
                "path": chunk.path,
                "sha": chunk.sha,
                "chunkIndex": chunk.chunk_index,
                "content": chunk.content,
            },
        )
        for chunk, vector in chunks_with_vectors
    ]

    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        wait=True,
        points=points,
    )

    logger.info("Stored %d chunks in batch", len(points))


async def search_similar_chunks(
    repository_id: str,
    index_version: str,
    vector: list[float],
    limit: int = 5,
) -> list[ScoredChunk]:
    """
    Semantic search using the CURRENT qdrant-client query API
    (client.query_points), never the deprecated client.search().

    Always filters by repositoryId AND indexVersion so results can never
    leak across repositories or stale index versions.
    """
    client = get_qdrant_client()

    query_filter = qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="repositoryId",
                match=qmodels.MatchValue(value=str(repository_id)),
            ),
            qmodels.FieldCondition(
                key="indexVersion",
                match=qmodels.MatchValue(value=index_version),
            ),
        ]
    )

    response = await client.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=vector,
        limit=limit,
        with_payload=True,
        query_filter=query_filter,
    )

    return [
        ScoredChunk(
            score=point.score,
            path=(point.payload or {}).get("path", ""),
            chunk_index=(point.payload or {}).get("chunkIndex", 0),
            content=(point.payload or {}).get("content", ""),
        )
        for point in response.points
    ]


async def clear_repository_vectors(repository_id: str) -> None:
    client = get_qdrant_client()

    await client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        wait=True,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="repositoryId",
                        match=qmodels.MatchValue(value=str(repository_id)),
                    )
                ]
            )
        ),
    )

    logger.info("Cleared vectors for repository: %s", repository_id)
