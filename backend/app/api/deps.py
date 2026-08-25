"""
Shared FastAPI dependencies: JWT authentication.

Equivalent to the original middleware/authMiddleware.js. Extracts and
validates the Bearer token, attaching the decoded user id to the request
via dependency injection (`current_user_id`).
"""

# ruff: noqa: B008

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.logging import logger
from app.core.security import JWTError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """
    Extract and validate the JWT Bearer token.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Unauthorized")

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except JWTError as error:
        logger.warning("JWT authentication failed: %s", error)
        raise UnauthorizedError("Unauthorized") from error

    user_id = payload.get("id")

    if not user_id:
        raise UnauthorizedError("Unauthorized")

    return user_id
