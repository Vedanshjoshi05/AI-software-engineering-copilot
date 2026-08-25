from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

IndexingStatus = Literal["not_indexed", "indexing", "ready", "failed"]


class CreateRepositoryRequest(BaseModel):
    githubUrl: str = Field(..., description="Full GitHub repository URL")

    @field_validator("githubUrl")
    @classmethod
    def validate_github_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("githubUrl is required")
        if "github.com" not in value:
            raise ValueError("githubUrl must be a valid GitHub repository URL")
        return value


class RepositoryOut(BaseModel):
    id: str
    owner: str
    name: str
    description: str = ""
    githubUrl: str
    isPrivate: bool = False
    defaultBranch: str = "main"
    activeIndexVersion: str | None = None
    indexingStatus: IndexingStatus = "not_indexed"
    indexingStartedAt: datetime | None = None
    indexingProgress: int = 0
    indexedFiles: int = 0
    indexedChunks: int = 0
    indexingError: str | None = None
    lastIndexedAt: datetime | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class CreateRepositoryResponse(BaseModel):
    success: bool = True
    message: str = "Repository created successfully"
    repository: RepositoryOut


class ListRepositoriesResponse(BaseModel):
    success: bool = True
    count: int
    repositories: list[RepositoryOut]


class GetRepositoryResponse(BaseModel):
    success: bool = True
    repository: RepositoryOut


class DeleteRepositoryResponse(BaseModel):
    success: bool = True
    message: str = "Repository deleted successfully"
