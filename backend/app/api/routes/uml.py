"""UML generation route — equivalent of controller/umlController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import UmlResponse
from app.services.ai.ai_service import generate_repository_uml

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/uml", response_model=UmlResponse)
async def generate_uml(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> UmlResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository must be indexed before generating UML")

    result = await generate_repository_uml(repository_id, limit=20)

    return UmlResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        report=result["report"],
        mermaid=result["mermaid"],
        sources=result["sources"],
    )
