"""
Centralized exception types and FastAPI exception handlers.

All error responses follow the consistent shape:

    { "success": false, "message": "..." }

Stack traces and internal details are never sent to clients; they are
logged server-side only.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger


class AppError(Exception):
    """Base application error with an HTTP status code and safe message."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationAppError(AppError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"success": False, "message": message}
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        logger.warning(
            "AppError on %s %s: %s", request.method, request.url.path, exc.message
        )
        return _error_response(exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        logger.info(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        # Build a concise, safe message without leaking internals
        first_error = exc.errors()[0] if exc.errors() else None
        message = "Invalid request data"
        if first_error:
            loc = ".".join(str(p) for p in first_error.get("loc", []) if p != "body")
            message = (
                f"Invalid value for '{loc}'" if loc else first_error.get("msg", message)
            )
        return _error_response(message, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _error_response(detail, exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            repr(exc),
            exc_info=True,
        )
        return _error_response(
            "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR
        )
