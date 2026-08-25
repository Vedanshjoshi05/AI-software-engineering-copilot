"""Security analysis route — equivalent of controller/securityController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import SecurityAnalysisResponse
from app.services.ai.ai_service import analyze_repository_security

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/security", response_model=SecurityAnalysisResponse)
async def analyze_security(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> SecurityAnalysisResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository must be indexed before security analysis")

    result = await analyze_repository_security(repository_id, limit=12)

    return SecurityAnalysisResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        analysis=result["analysis"],
        sources=result["sources"],
    )
