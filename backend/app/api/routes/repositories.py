"""
Repository CRUD routes — equivalent of the repository handlers in
routes/repositoryRoutes.js + controller/repositoryController.js.

Preserves: GitHub metadata caching via Redis (graceful degradation),
duplicate-import protection, and strict ownership enforcement (a user can
never access another user's repository).
"""

from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.logging import logger
from app.db.redis import cache_get, cache_set
from app.models import repository as repository_model
from app.schemas.repository import (
    CreateRepositoryRequest,
    CreateRepositoryResponse,
    DeleteRepositoryResponse,
    GetRepositoryResponse,
    ListRepositoriesResponse,
    RepositoryOut,
)
from app.services.github.github_service import parse_github_url

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


def _to_out(doc: dict) -> RepositoryOut:
    serialized = repository_model.serialize_repository(doc)
    return RepositoryOut(**serialized)


@router.post("", response_model=CreateRepositoryResponse, status_code=201)
async def create_repository(
    payload: CreateRepositoryRequest, user_id: str = Depends(get_current_user_id)
) -> CreateRepositoryResponse:
    try:
        github_owner, repo_name = parse_github_url(payload.githubUrl)
    except ValueError as error:
        raise ValidationAppError(str(error)) from error

    existing = await repository_model.find_repository_by_owner_and_url(
        user_id, payload.githubUrl
    )
    if existing:
        raise ConflictError("Repository already imported")

    cache_key = f"github:repo:{github_owner}:{repo_name}"
    cached = await cache_get(cache_key)

    if cached:
        logger.info("Redis cache HIT")
        github_data = json.loads(cached)
    else:
        logger.info("Redis cache MISS")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{settings.GITHUB_API_BASE_URL}/repos/{github_owner}/{repo_name}",
                    headers=(
                        {"Authorization": f"Bearer {settings.GITHUB_TOKEN}"}
                        if settings.GITHUB_TOKEN
                        else {}
                    ),
                )
                if response.status_code == 404:
                    raise NotFoundError("GitHub repository not found or not accessible")
                response.raise_for_status()
                github_data = response.json()
        except httpx.HTTPStatusError as error:
            raise ValidationAppError(f"GitHub API error: {error}") from error

        await cache_set(
            cache_key, json.dumps(github_data), settings.REDIS_CACHE_TTL_SECONDS
        )

    repository_doc = await repository_model.create_repository(
        owner_id=user_id,
        github_url=payload.githubUrl,
        name=github_data.get("name", repo_name),
        description=github_data.get("description") or "",
        is_private=bool(github_data.get("private", False)),
        default_branch=github_data.get("default_branch", "main"),
    )

    return CreateRepositoryResponse(repository=_to_out(repository_doc))


@router.get("", response_model=ListRepositoriesResponse)
async def list_repositories(
    user_id: str = Depends(get_current_user_id),
) -> ListRepositoriesResponse:
    docs = await repository_model.list_repositories_for_owner(user_id)
    repos = [_to_out(doc) for doc in docs]
    return ListRepositoriesResponse(count=len(repos), repositories=repos)


@router.get("/{repository_id}", response_model=GetRepositoryResponse)
async def get_repository(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> GetRepositoryResponse:
    doc = await repository_model.find_repository_for_owner(repository_id, user_id)
    if not doc:
        raise NotFoundError("Repository not found")
    return GetRepositoryResponse(repository=_to_out(doc))


@router.delete("/{repository_id}", response_model=DeleteRepositoryResponse)
async def delete_repository(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> DeleteRepositoryResponse:
    doc = await repository_model.find_repository_for_owner(repository_id, user_id)
    if not doc:
        raise NotFoundError("Repository not found")

    await repository_model.delete_repository(repository_id)
    return DeleteRepositoryResponse()
