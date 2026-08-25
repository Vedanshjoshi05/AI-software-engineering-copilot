"""Test generation route — equivalent of controller/testGenerationController.js."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.models import repository as repository_model
from app.schemas.ai import TestGenerationResponse
from app.services.ai.ai_service import generate_repository_tests

router = APIRouter(prefix="/api/repositories", tags=["AI Features"])


@router.post("/{repository_id}/tests", response_model=TestGenerationResponse)
async def generate_tests(
    repository_id: str, user_id: str = Depends(get_current_user_id)
) -> TestGenerationResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    if not repository.get("activeIndexVersion"):
        raise ConflictError("Repository must be indexed before generating tests")

    result = await generate_repository_tests(repository_id, limit=20)

    return TestGenerationResponse(
        repositoryId=repository_id,
        repository=repository["name"],
        summary=result["summary"],
        tests=result["tests"],
        sources=result["sources"],
    )
