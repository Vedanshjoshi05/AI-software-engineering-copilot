"""
Redis client wrapper with graceful degradation.

Equivalent to the original config/redis.js. The application must never
crash because Redis is temporarily unavailable -- every call site should
use the helper functions below, which swallow connection errors and log
a warning instead of raising.
"""

from __future__ import annotations

import redis.asyncio as redis_asyncio
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import logger

_client: redis_asyncio.Redis | None = None
_available: bool = False


async def connect_redis() -> None:
    global _client, _available
    try:
        _client = redis_asyncio.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            retry_on_timeout=False,
        )
        await _client.ping()
        _available = True
        logger.info("Redis connected successfully")
    except Exception as error:  # noqa: BLE001
        _available = False
        logger.warning(
            "Redis unavailable at startup, continuing without cache: %s", error
        )


async def close_redis() -> None:
    global _client, _available
    if _client is not None:
        try:
            await _client.close()
        except Exception as error:  # noqa: BLE001
            logger.warning("Error while closing Redis connection: %s", error)
    _client = None
    _available = False


async def cache_get(key: str) -> str | None:
    if not _client:
        return None
    try:
        value = await _client.get(key)
        return value if value is None else str(value)
    except RedisError as error:
        logger.warning("Redis GET failed for key '%s': %s", key, error)
        return None


async def cache_set(key: str, value: str, ttl_seconds: int | None = None) -> bool:
    if not _client:
        return False
    try:
        await _client.set(key, value, ex=ttl_seconds)
        return True
    except RedisError as error:
        logger.warning("Redis SET failed for key '%s': %s", key, error)
        return False


async def cache_delete(key: str) -> bool:
    if not _client:
        return False
    try:
        await _client.delete(key)
        return True
    except RedisError as error:
        logger.warning("Redis DELETE failed for key '%s': %s", key, error)
        return False


def is_available() -> bool:
    return _available


__all__ = [
    "cache_delete",
    "cache_get",
    "cache_set",
    "close_redis",
    "connect_redis",
    "is_available",
]
