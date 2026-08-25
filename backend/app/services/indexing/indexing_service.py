"""
Repository indexing pipeline — equivalent of services/repositoryIndexingService.js.

Runs asynchronously (as an asyncio background task kicked off by the route
handler) so the HTTP request returns 202 Accepted immediately rather than
blocking for the whole pipeline. Progress is persisted to MongoDB after
each chunk so GET /index-status always reflects current state.

NOTE on production scaling: asyncio.create_task() runs the job in the same
process as the web server, which is fine for a single instance / local
development. For multi-instance production deployments, replace the
`schedule_indexing()` call site with a real task queue (Celery, RQ, arq,
or SQS + worker) so indexing survives process restarts and scales
independently of the API. See README "Recommended Dockerization / Deployment".
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.core.logging import logger
from app.models import repository as repository_model
from app.services.chunking.chunking_service import chunk_repository_files
from app.services.embeddings.factory import get_embedding_provider
from app.services.github.ingestion_service import (
    fetch_repository_files,
    ingest_repository,
)
from app.services.vector.qdrant_service import store_chunk

EMBEDDING_DELAY_SECONDS = 0.15


async def index_repository(
    repository_id: str, github_owner: str, repo_name: str, branch: str
) -> dict:
    embedding_provider = get_embedding_provider()

    try:
        logger.info("Starting indexing: %s/%s", github_owner, repo_name)

        repository = await repository_model.find_repository_by_id(repository_id)
        if not repository:
            raise ValueError("Repository not found")

        await repository_model.update_repository(
            repository_id,
            {
                "indexingStatus": "indexing",
                "indexingStartedAt": datetime.now(timezone.utc),
                "indexingProgress": 0,
                "indexingError": None,
                "indexedFiles": 0,
                "indexedChunks": 0,
            },
        )
        logger.info("Indexing status: indexing")

        index_version = str(uuid.uuid4())
        logger.info("Creating index version: %s", index_version)

        eligible_files = await ingest_repository(github_owner, repo_name, branch)
        logger.info("Eligible files: %d", len(eligible_files))

        if not eligible_files:
            raise ValueError("No eligible source files found")

        from app.core.config import settings

        selected_files = eligible_files[: settings.MAX_FILES_PER_INDEX]
        logger.info("Files selected: %d", len(selected_files))

        files_with_content = await fetch_repository_files(
            github_owner, repo_name, selected_files
        )
        logger.info("Files downloaded: %d", len(files_with_content))

        if not files_with_content:
            raise ValueError("No repository files could be downloaded")

        chunks = chunk_repository_files(files_with_content)
        logger.info("Chunks created: %d", len(chunks))

        if not chunks:
            raise ValueError("No code chunks were created")

        indexed_chunks = 0
        failed_chunks: list[dict] = []
        last_saved_progress = 0

        for i, chunk in enumerate(chunks):
            try:
                vector = await embedding_provider.generate_embedding(chunk.content)
                await store_chunk(repository_id, chunk, vector, index_version)
                indexed_chunks += 1
                logger.info("Indexed %d/%d", indexed_chunks, len(chunks))
            except Exception as error:  # noqa: BLE001
                logger.warning(
                    "Failed to index %s chunk %d: %s",
                    chunk.path,
                    chunk.chunk_index,
                    error,
                )
                failed_chunks.append(
                    {
                        "path": chunk.path,
                        "chunkIndex": chunk.chunk_index,
                        "error": str(error),
                    }
                )

            processed = i + 1
            progress = int((processed / len(chunks)) * 100)

            if progress > last_saved_progress:
                await repository_model.update_repository(
                    repository_id,
                    {"indexingProgress": progress, "indexedChunks": indexed_chunks},
                )
                last_saved_progress = progress
                logger.info("Indexing progress: %d%%", progress)

            if i < len(chunks) - 1:
                await asyncio.sleep(EMBEDDING_DELAY_SECONDS)

        if indexed_chunks != len(chunks):
            raise ValueError(
                f"Indexing incomplete: {indexed_chunks}/{len(chunks)} chunks indexed"
            )

        await repository_model.update_repository(
            repository_id,
            {
                "activeIndexVersion": index_version,
                "indexingStatus": "ready",
                "indexingStartedAt": None,
                "indexingProgress": 100,
                "indexedFiles": len(files_with_content),
                "indexedChunks": indexed_chunks,
                "indexingError": None,
                "lastIndexedAt": datetime.now(timezone.utc),
            },
        )
        logger.info("Activated index version: %s", index_version)
        logger.info("Indexing status: ready")
        logger.info("Repository indexing completed")

        return {
            "eligibleFiles": len(eligible_files),
            "selectedFiles": len(selected_files),
            "files": len(files_with_content),
            "chunks": len(chunks),
            "indexedChunks": indexed_chunks,
            "failedChunks": len(failed_chunks),
            "indexVersion": index_version,
        }
    except Exception as error:
        logger.error("Repository indexing failed: %s", error)
        try:
            await repository_model.update_repository(
                repository_id,
                {
                    "indexingStatus": "failed",
                    "indexingStartedAt": None,
                    "indexingError": str(error),
                },
            )
        except Exception as update_error:  # noqa: BLE001
            logger.error("Failed to update indexing status: %s", update_error)
        raise


def schedule_indexing(
    repository_id: str, github_owner: str, repo_name: str, branch: str
) -> None:
    """Fire-and-forget background task, matching the original
    `indexRepository(...).catch(...)` pattern in indexingController.js."""

    async def _run() -> None:
        try:
            await index_repository(repository_id, github_owner, repo_name, branch)
        except Exception as error:  # noqa: BLE001
            logger.error("Background indexing failed for %s: %s", repository_id, error)

    asyncio.create_task(_run())
