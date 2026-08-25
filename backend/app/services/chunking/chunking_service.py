"""
Code-aware chunking — equivalent of services/codeChunkingService.js.

Splits each file's content into overlapping chunks of configurable size,
attaching metadata (path, sha, chunkIndex, content) needed later for
Qdrant payloads and citation in AI responses.
"""

from __future__ import annotations

from app.core.config import settings
from app.services.github.ingestion_service import RepoFile
from app.services.vector.qdrant_service import CodeChunkPayload


def chunk_file(file: RepoFile) -> list[CodeChunkPayload]:
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP

    chunks: list[CodeChunkPayload] = []
    content = file.content
    start = 0
    chunk_index = 0

    if not content:
        return chunks

    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk_content = content[start:end]

        chunks.append(
            CodeChunkPayload(
                path=file.path,
                sha=file.sha,
                chunk_index=chunk_index,
                content=chunk_content,
            )
        )

        chunk_index += 1

        if end == len(content):
            break

        start = end - overlap

    return chunks


def chunk_repository_files(files: list[RepoFile]) -> list[CodeChunkPayload]:
    all_chunks: list[CodeChunkPayload] = []
    for file in files:
        all_chunks.extend(chunk_file(file))
    return all_chunks
