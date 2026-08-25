"""
FastAPI application entrypoint — equivalent of app.js + server.js.

Wires together: DB/cache/vector-store lifecycle, CORS, structured request
logging (method/path/status/duration/request ID), centralized exception
handling, the health endpoint, and every route module.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    bugs,
    deployment,
    documentation,
    explanation,
    indexing,
    optimization,
    rag,
    repositories,
    security,
    tests,
    uml,
)
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.db.mongodb import close_mongo, connect_mongo
from app.db.qdrant import close_qdrant, connect_qdrant
from app.db.redis import close_redis, connect_redis
from app.services.vector.qdrant_service import create_code_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)

    await connect_mongo()
    await connect_redis()
    await connect_qdrant()

    try:
        await create_code_collection()
    except Exception as error:  # noqa: BLE001
        logger.error("Failed to ensure Qdrant collection exists: %s", error)

    logger.info("Startup complete")
    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    await close_mongo()
    await close_redis()
    await close_qdrant()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered platform that ingests GitHub repositories and provides "
        "RAG-backed software engineering assistance: code explanation, bug "
        "detection, security analysis, optimization, test generation, API "
        "documentation, UML generation, and deployment planning."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "%s %s -> %d (%sms) [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )

    return response


@app.get("/health", tags=["System"], summary="Health check")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", tags=["System"], summary="Root")
async def root() -> dict:
    return {"success": True, "message": f"Welcome to {settings.APP_NAME}"}


app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(indexing.router)
app.include_router(rag.router)
app.include_router(explanation.router)
app.include_router(bugs.router)
app.include_router(security.router)
app.include_router(optimization.router)
app.include_router(uml.router)
app.include_router(tests.router)
app.include_router(documentation.router)
app.include_router(deployment.router)
