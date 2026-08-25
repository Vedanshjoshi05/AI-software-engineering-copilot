"""Deployment generation route — equivalent of controller/deploymentController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import DeploymentResponse
from app.services.ai.ai_service import generate_repository_deployment

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/deployment", response_model=DeploymentResponse)
async def generate_deployment(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> DeploymentResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError(
            "Repository must be indexed before generating deployment configuration"
        )

    result = await generate_repository_deployment(repository_id, limit=20)

    return DeploymentResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        report=result["report"],
        dockerfile=result["dockerfile"],
        dockerignore=result["dockerignore"],
        githubActions=result["githubActions"],
        sources=result["sources"],
    )
