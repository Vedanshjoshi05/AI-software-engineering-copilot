"""
RAG route — equivalent of controller/ragController.js.

SECURITY FIX vs. original: the original askRepositoryQuestion() called
answerRepositoryQuestion() with only the repositoryId (Repository.findById,
no owner filter), so any authenticated user could query another user's
repository. Every other route in the app enforces ownership; this route
now does too, closing that gap.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import NotFoundError
from app.models import repository as repository_model
from app.schemas.rag import AskQuestionRequest, AskQuestionResponse
from app.services.rag.rag_service import answer_repository_question

router = APIRouter(prefix="/api/repositories", tags=["RAG"])


@router.post("/{repository_id}/ask", response_model=AskQuestionResponse)
async def ask_repository_question(
    repository_id: str,
    payload: AskQuestionRequest,
    user_id: str = Depends(get_current_user_id),
) -> AskQuestionResponse:
    repository = await repository_model.find_repository_for_owner(
        repository_id, user_id
    )
    if not repository:
        raise NotFoundError("Repository not found")

    result = await answer_repository_question(repository_id, payload.question)
    return AskQuestionResponse(answer=result["answer"], sources=result["sources"])
