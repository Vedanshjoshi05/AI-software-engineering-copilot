"""
RAG service — equivalent of answerRepositoryQuestion() in ragService.js.

Ties RetrievalService + PromptService + LLMProvider together. Kept as
free-form text (rather than structured JSON) since a natural-language
answer is the most useful shape for a direct Q&A feature and matches the
original API contract exactly.
"""

from __future__ import annotations

from app.services.ai.factory import get_llm_provider
from app.services.rag.prompt_service import build_rag_prompt
from app.services.rag.retrieval_service import (
    build_context,
    retrieve_repository_context,
    sources_from_context,
)


async def answer_repository_question(
    repository_id: str, question: str, limit: int = 5
) -> dict:
    retrieval = await retrieve_repository_context(repository_id, question, limit)

    if not retrieval.context:
        return {
            "answer": "I could not find relevant code in the indexed repository context.",
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = build_rag_prompt(
        retrieval.repository["name"], repository_context, question
    )

    llm = get_llm_provider()
    answer = await llm.generate(prompt)

    return {"answer": answer, "sources": sources_from_context(retrieval.context)}
