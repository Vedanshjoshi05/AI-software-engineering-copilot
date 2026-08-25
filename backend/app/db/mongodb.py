"""
MongoDB connection using Motor (async driver).

Equivalent to the original config/db.js (Mongoose connect). We use raw
Motor collections rather than an ODM to keep the dependency footprint
small and the migration mapping explicit (see models/user.py and
models/repository.py for the schema-equivalent dataclasses + helpers).
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    global _client, _db
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI, serverSelectionTimeoutMS=8000
        )
        # Force a round trip to verify connectivity, mirroring mongoose.connect()'s
        # fail-fast behavior.
        await _client.admin.command("ping")
        _db = _client.get_database(settings.MONGODB_DB_NAME)
        await _ensure_indexes(_db)
        logger.info("MongoDB connected")
    except Exception as error:
        logger.error("Error connecting to MongoDB: %s", error)
        raise


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.repositories.create_index([("owner", 1), ("githubUrl", 1)], unique=True)


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "MongoDB has not been initialized. Call connect_mongo() first."
        )
    return _db
