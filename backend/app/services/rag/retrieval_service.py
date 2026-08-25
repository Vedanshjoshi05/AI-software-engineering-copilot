"""
RetrievalService — shared semantic retrieval used by RAG Q&A and every AI
feature (explain, bugs, security, optimization, tests, docs, UML,
deployment). Centralizing this avoids duplicating retrieval logic inside
every feature, per the migration requirements.

Equivalent to retrieveRepositoryContext() in the original ragService.js.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import logger
from app.models import repository as repository_model
from app.services.embeddings.factory import get_embedding_provider
from app.services.vector.qdrant_service import ScoredChunk, search_similar_chunks


@dataclass
class RetrievedChunk:
    score: float
    path: str
    chunk_index: int
    content: str


@dataclass
class RetrievalResult:
    repository: dict[str, Any]
    question: str
    context: list[RetrievedChunk]


async def retrieve_repository_context(
    repository_id: str, question: str, limit: int = 5
) -> RetrievalResult:
    repository = await repository_model.find_repository_by_id(repository_id)

    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository has not been indexed yet")

    logger.info("Active index version: %s", repository["activeIndexVersion"])

    embedding_provider = get_embedding_provider()
    question_vector = await embedding_provider.generate_embedding(question)
    logger.info("Question embedding dimension: %d", len(question_vector))

    results: list[ScoredChunk] = await search_similar_chunks(
        repository_id=str(repository["_id"]),
        index_version=repository["activeIndexVersion"],
        vector=question_vector,
        limit=limit,
    )
    logger.info("Relevant chunks found: %d", len(results))

    context = [
        RetrievedChunk(
            score=r.score, path=r.path, chunk_index=r.chunk_index, content=r.content
        )
        for r in results
    ]

    return RetrievalResult(repository=repository, question=question, context=context)


def build_context(chunks: list[RetrievedChunk]) -> str:
    sections = []
    for chunk in chunks:
        sections.append(
            f"\n--- CONTEXT {chunks.index(chunk) + 1} ---\n\n"
            f"FILE:\n{chunk.path}\n\n"
            f"CHUNK:\n{chunk.chunk_index}\n\n"
            f"CODE:\n{chunk.content}\n"
        )
    return "\n".join(sections)


def sources_from_context(chunks: list[RetrievedChunk]) -> list[dict]:
    return [
        {"path": c.path, "chunkIndex": c.chunk_index, "score": c.score} for c in chunks
    ]
