"""API documentation route — equivalent of controller/apiDocumentationController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import ApiDocumentationResponse
from app.services.ai.ai_service import generate_api_documentation

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/documentation", response_model=ApiDocumentationResponse)
async def generate_documentation(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> ApiDocumentationResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError(
            "Repository must be indexed before generating API documentation"
        )

    result = await generate_api_documentation(repository_id, limit=20)

    return ApiDocumentationResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        documentation=result["documentation"],
        sources=result["sources"],
    )
