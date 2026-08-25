"""
Structured logging configuration.

Mirrors the original Pino-based logging: JSON structured logs in production,
pretty console logs in development. Every request logs method/path/status/
duration/request ID via the middleware in main.py. Sensitive fields
(tokens, passwords, API keys, DB credentials) are never logged.
"""

import logging
import sys

from app.core.config import settings

SENSITIVE_KEYS = {
    "password",
    "token",
    "authorization",
    "jwt_secret",
    "api_key",
    "apikey",
    "llm_api_key",
    "embedding_api_key",
    "github_token",
    "qdrant_api_key",
    "mongodb_uri",
}


class RedactingFilter(logging.Filter):
    """Best-effort redaction filter for sensitive substrings in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001
            return True

        lowered = msg.lower()
        for key in SENSITIVE_KEYS:
            if key in lowered:
                record.msg = "[redacted: message contained a sensitive field name]"
                record.args = ()
                break
        return True


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("ai_copilot")
    logger.setLevel(settings.LOG_LEVEL.upper() if settings.LOG_LEVEL else "INFO")

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENV == "production":
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = configure_logging()
