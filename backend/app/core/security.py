"""
Security utilities: password hashing (bcrypt) and JWT creation/validation.

Mirrors the original Node behavior:
- bcryptjs with a salt round of 10 for hashing (model/user.js pre-save hook)
- jsonwebtoken sign/verify with a single `id` claim (authController.js)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

BCRYPT_ROUNDS = 10


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    """Create a JWT with a single `id` claim, matching the original contract."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.jwt_expires_seconds)

    payload: dict[str, Any] = {
        "id": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure (expired/invalid/tampered)."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


__all__ = [
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
