from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

IndexingStatus = Literal["not_indexed", "indexing", "ready", "failed"]


class StartIndexingResponse(BaseModel):
    success: bool = True
    message: str = "Repository indexing started"
    repositoryId: str
    status: IndexingStatus = "indexing"


class IndexingAlreadyRunningResponse(BaseModel):
    success: bool = False
    message: str = "Repository is already being indexed"
    status: IndexingStatus = "indexing"
    progress: int


class IndexStatusResponse(BaseModel):
    success: bool = True
    repositoryId: str
    name: str
    status: IndexingStatus
    progress: int
    indexedFiles: int
    indexedChunks: int
    error: str | None = None
    indexingStartedAt: datetime | None = None
    lastIndexedAt: datetime | None = None
    ready: bool
    activeIndexVersion: str | None = None
