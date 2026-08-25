"""
User model — equivalent of the original model/user.js Mongoose schema.

Fields: name, email (unique, lowercase), password (bcrypt hash), avatar,
createdAt/updatedAt (timestamps).

We use plain Motor collections + a lightweight dataclass-style helper
rather than an ODM, keeping the migration mapping explicit and dependency
footprint small.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.security import hash_password, verify_password
from app.db.mongodb import get_db

COLLECTION_NAME = "users"


def users_collection() -> AsyncIOMotorCollection:
    return get_db()[COLLECTION_NAME]


def serialize_user(
    doc: dict[str, Any], include_password: bool = False
) -> dict[str, Any]:
    """Convert a Mongo user document into a JSON-safe dict."""
    result = {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "avatar": doc.get("avatar", ""),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }
    if include_password:
        result["password"] = doc.get("password")
    return result


async def find_user_by_email(email: str) -> dict[str, Any] | None:
    return await users_collection().find_one({"email": email.lower().strip()})


async def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    if not ObjectId.is_valid(user_id):
        return None
    return await users_collection().find_one({"_id": ObjectId(user_id)})


async def create_user(
    name: str, email: str, password: str, avatar: str = ""
) -> dict[str, Any]:
    """Create a user with a bcrypt-hashed password, mirroring the pre('save') hook."""
    now = datetime.now(timezone.utc)
    document = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hash_password(password),
        "avatar": avatar,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await users_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return document


def compare_password(user_doc: dict[str, Any], candidate_password: str) -> bool:
    return verify_password(candidate_password, user_doc.get("password", ""))
