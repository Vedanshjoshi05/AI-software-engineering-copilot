"""
Repository model — equivalent of the original model/repository.js.

Preserves the indexing state machine (not_indexed / indexing / ready / failed),
progress tracking fields, and the compound unique index on (owner, githubUrl)
that prevents a user from importing the same repository twice.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.db.mongodb import get_db

COLLECTION_NAME = "repositories"

IndexingStatus = Literal["not_indexed", "indexing", "ready", "failed"]


def repositories_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


def serialize_repository(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "owner": str(doc["owner"]),
        "name": doc.get("name"),
        "description": doc.get("description", ""),
        "githubUrl": doc.get("githubUrl"),
        "isPrivate": doc.get("isPrivate", False),
        "defaultBranch": doc.get("defaultBranch", "main"),
        "activeIndexVersion": doc.get("activeIndexVersion"),
        "indexingStatus": doc.get("indexingStatus", "not_indexed"),
        "indexingStartedAt": doc.get("indexingStartedAt"),
        "indexingProgress": doc.get("indexingProgress", 0),
        "indexedFiles": doc.get("indexedFiles", 0),
        "indexedChunks": doc.get("indexedChunks", 0),
        "indexingError": doc.get("indexingError"),
        "lastIndexedAt": doc.get("lastIndexedAt"),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }


async def find_repository_by_owner_and_url(
    owner_id: str, github_url: str
) -> dict[str, Any] | None:
    return await repositories_collection().find_one(
        {"owner": ObjectId(owner_id), "githubUrl": github_url}
    )


async def find_repository_for_owner(
    repository_id: str, owner_id: str
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(repository_id):
        return None
    return await repositories_collection().find_one(
        {"_id": ObjectId(repository_id), "owner": ObjectId(owner_id)}
    )


async def find_repository_by_id(repository_id: str) -> dict[str, Any] | None:
    if not ObjectId.is_valid(repository_id):
        return None
    return await repositories_collection().find_one({"_id": ObjectId(repository_id)})


async def list_repositories_for_owner(owner_id: str) -> list[dict[str, Any]]:
    cursor = (
        repositories_collection()
        .find({"owner": ObjectId(owner_id)})
        .sort("createdAt", -1)
    )
    return await cursor.to_list(length=None)


async def create_repository(
    owner_id: str,
    github_url: str,
    name: str,
    description: str,
    is_private: bool,
    default_branch: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    document = {
        "owner": ObjectId(owner_id),
        "githubUrl": github_url,
        "name": name,
        "description": description or "",
        "isPrivate": is_private,
        "defaultBranch": default_branch or "main",
        "activeIndexVersion": None,
        "indexingStatus": "not_indexed",
        "indexingStartedAt": None,
        "indexingProgress": 0,
        "indexedFiles": 0,
        "indexedChunks": 0,
        "indexingError": None,
        "lastIndexedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await repositories_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return document


async def update_repository(repository_id: str, updates: dict[str, Any]) -> None:
    updates = {**updates, "updatedAt": datetime.now(timezone.utc)}
    await repositories_collection().update_one(
        {"_id": ObjectId(repository_id)}, {"$set": updates}
    )


async def delete_repository(repository_id: str) -> None:
    await repositories_collection().delete_one({"_id": ObjectId(repository_id)})
