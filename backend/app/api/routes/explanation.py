"""Code explanation route — equivalent of controller/codeExplanationController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.rag import ExplainCodeRequest, ExplainCodeResponse
from app.services.ai.ai_service import explain_code

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/explain", response_model=ExplainCodeResponse)
async def explain_repository_code(
    repository_id: str,
    payload: ExplainCodeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ExplainCodeResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository must be indexed before code explanation")

    target = payload.target.strip()
    result = await explain_code(repository_id, target, limit=8)

    return ExplainCodeResponse(
        target=target, explanation=result["explanation"], sources=result["sources"]
    )
