"""Bug detection route — equivalent of controller/bugDetectionController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import BugDetectionResponse
from app.services.ai.ai_service import detect_repository_bugs

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/bugs", response_model=BugDetectionResponse)
async def detect_bugs(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> BugDetectionResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository must be indexed before bug detection")

    result = await detect_repository_bugs(repository_id, limit=12)

    return BugDetectionResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        analysis=result["analysis"],
        sources=result["sources"],
    )
