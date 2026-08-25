"""
Repository ingestion — equivalent of services/repositoryIngestionService.js.

Fetches the repository tree, filters to eligible source files under the
configured size limit, prioritizes the most relevant directories, and
downloads file contents in small concurrent batches (so a large repo does
not fire hundreds of simultaneous GitHub requests at once).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.github.github_service import (
    filter_source_files,
    get_file_content,
    get_repository_tree,
)

PRIORITY_DIRECTORIES = (
    "src/",
    "packages/",
    "controllers/",
    "controller/",
    "services/",
    "routes/",
    "middleware/",
    "models/",
    "model/",
    "components/",
    "hooks/",
    "utils/",
    "lib/",
)

DOWNLOAD_BATCH_SIZE = 5


@dataclass
class RepoFile:
    path: str
    sha: str
    size: int
    content: str


def _priority_of(path: str) -> int:
    lowered = path.lower()
    for index, directory in enumerate(PRIORITY_DIRECTORIES):
        if lowered.startswith(directory):
            return index
    return len(PRIORITY_DIRECTORIES)


def _prioritize_source_files(files: list[dict]) -> list[dict]:
    return sorted(files, key=lambda f: _priority_of(f["path"]))


async def ingest_repository(owner: str, repo: str, branch: str) -> list[dict]:
    """Return eligible, size-filtered, priority-sorted file entries (metadata only)."""
    tree_data = await get_repository_tree(owner, repo, branch)
    tree = tree_data.get("tree", [])

    source_files = filter_source_files(tree)
    eligible_files = [
        f
        for f in source_files
        if f.get("size") and f["size"] <= settings.MAX_FILE_SIZE_BYTES
    ]
    prioritized = _prioritize_source_files(eligible_files)

    logger.info("Total repository items: %d", len(tree))
    logger.info("Source files: %d", len(source_files))
    logger.info("Eligible files: %d", len(eligible_files))

    return prioritized


async def fetch_repository_files(
    owner: str, repo: str, files: list[dict]
) -> list[RepoFile]:
    """Download file contents in small concurrent batches, dropping any file
    that fails to download rather than failing the whole indexing job."""
    results: list[RepoFile] = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for i in range(0, len(files), DOWNLOAD_BATCH_SIZE):
            batch = files[i : i + DOWNLOAD_BATCH_SIZE]

            async def _fetch_one(file: dict) -> RepoFile | None:
                try:
                    content = await get_file_content(
                        owner, repo, file["sha"], client=client
                    )
                    return RepoFile(
                        path=file["path"],
                        sha=file["sha"],
                        size=file.get("size", 0),
                        content=content,
                    )
                except Exception as error:  # noqa: BLE001
                    logger.warning("Failed to fetch %s: %s", file["path"], error)
                    return None

            batch_results = await asyncio.gather(*(_fetch_one(f) for f in batch))
            results.extend(r for r in batch_results if r is not None)

    return results
