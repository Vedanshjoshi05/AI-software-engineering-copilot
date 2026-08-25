"""
Indexing routes — equivalent of controller/indexingController.js.

POST /index starts a background indexing job and returns 202 Accepted
immediately. GET /index-status reports live progress, including detection
of stale ("stuck") indexing jobs older than INDEXING_TIMEOUT_MINUTES.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.logging import logger
from app.models import repository as repository_model
from app.schemas.indexing import IndexStatusResponse, StartIndexingResponse
from app.services.github.github_service import parse_github_url
from app.services.indexing.indexing_service import schedule_indexing

router = APIRouter(prefix="/api/repositories", tags=["Indexing"])


def _is_stale(started_at: datetime | None) -> bool:
    if not started_at:
        return False
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    elapsed = datetime.now(timezone.utc) - started_at
    return elapsed > timedelta(minutes=settings.INDEXING_TIMEOUT_MINUTES)


@router.post(
    "/{repository_id}/index", response_model=StartIndexingResponse, status_code=202
)
async def start_repository_indexing(
    repository_id: str, response: Response, user_id: str = Depends(get_current_user_id)
) -> StartIndexingResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if repository.get("indexingStatus") == "indexing":
        if not _is_stale(repository.get("indexingStartedAt")):
            raise ConflictError("Repository is already being indexed")

        logger.warning(
            "Stale indexing job detected for repository %s. Resetting state.",
            repository_id,
        )
        await repository_model.update_repository(
            repository_id,
            {
                "indexingStatus": "failed",
                "indexingStartedAt": None,
                "indexingError": "Previous indexing job timed out and was marked as failed.",
            },
        )

    try:
        github_owner, repo_name = parse_github_url(repository["githubUrl"])
    except ValueError as error:
        raise ValidationAppError("Invalid GitHub repository URL") from error

    schedule_indexing(
        repository_id, github_owner, repo_name, repository.get("defaultBranch", "main")
    )

    return StartIndexingResponse(repositoryId=repository_id)


@router.get("/{repository_id}/index-status", response_model=IndexStatusResponse)
async def get_repository_index_status(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> IndexStatusResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    status = repository.get("indexingStatus", "not_indexed")

    if status == "indexing" and _is_stale(repository.get("indexingStartedAt")):
        await repository_model.update_repository(
            repository_id,
            {
                "indexingStatus": "failed",
                "indexingStartedAt": None,
                "indexingError": "Previous indexing job timed out and was marked as failed.",
            },
        )
        status = "failed"

    return IndexStatusResponse(
        repositoryId=repository_id,
        name=repository["name"],
        status=status,
        progress=repository.get("indexingProgress", 0),
        indexedFiles=repository.get("indexedFiles", 0),
        indexedChunks=repository.get("indexedChunks", 0),
        error=repository.get("indexingError"),
        indexingStartedAt=repository.get("indexingStartedAt"),
        lastIndexedAt=repository.get("lastIndexedAt"),
        ready=status == "ready",
        activeIndexVersion=repository.get("activeIndexVersion"),
    )
