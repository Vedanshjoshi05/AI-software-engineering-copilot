from __future__ import annotations

from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SourceReference(BaseModel):
    path: str
    chunkIndex: int
    score: float


class AskQuestionResponse(BaseModel):
    success: bool = True
    answer: str
    sources: list[SourceReference]


class ExplainCodeRequest(BaseModel):
    target: str = Field(
        ..., min_length=1, description="File, function, class, or feature to explain"
    )


class ExplainCodeResponse(BaseModel):
    success: bool = True
    target: str
    explanation: str
    sources: list[SourceReference]
