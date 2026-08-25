"""
Shared pytest fixtures.

Every external service is mocked so the test suite never depends on real
external APIs:

- MongoDB   -> mongomock-motor (in-memory async Mongo)
- Redis     -> fakeredis (in-memory async Redis)
- Qdrant    -> real qdrant-client pointed at an in-memory instance
               (location=":memory:"), so query_points()/upsert() behave
               exactly like production without a running server.
- GitHub    -> respx intercepting httpx calls to api.github.com
- LLM       -> FakeLLMProvider (canned text / canned structured objects)
- Embeddings-> FakeEmbeddingProvider (deterministic small vectors)
"""

from __future__ import annotations

import base64
from typing import TypeVar

import fakeredis.aioredis
import httpx
import pytest
import pytest_asyncio
import respx
from mongomock_motor import AsyncMongoMockClient
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient

import app.db.mongodb as mongodb_module
import app.db.qdrant as qdrant_module
import app.db.redis as redis_module
from app.core.config import settings
from app.main import app as fastapi_app
from app.services.ai.llm_provider import LLMProvider
from app.services.embeddings.provider import EmbeddingProvider
from app.services.vector.qdrant_service import create_code_collection

TSchema = TypeVar("TSchema", bound=BaseModel)

GITHUB_OWNER = "octocat"
GITHUB_REPO = "hello-world"
GITHUB_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"


# ----------------------------------------------------------------------
# Fake AI providers
# ----------------------------------------------------------------------
class FakeLLMProvider(LLMProvider):
    def __init__(self):
        self.structured_responses: dict[str, BaseModel] = {}
        self.generate_response = (
            "This is a generated answer based on the repository context."
        )
        self.raise_on_generate: Exception | None = None

    async def generate(self, prompt: str) -> str:
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.generate_response

    async def generate_structured(self, prompt: str, schema: type[TSchema]) -> TSchema:
        canned = self.structured_responses.get(schema.__name__)
        if canned is not None:
            return canned
        return _build_minimal_instance(schema)


def _build_minimal_instance(schema: type[TSchema]) -> TSchema:
    """Build a schema instance using only its required fields with simple
    placeholder values, for schemas without an explicit canned fixture."""
    values: dict = {}
    for name, field in schema.model_fields.items():
        if not field.is_required():
            continue
        annotation = field.annotation
        if annotation is str:
            values[name] = f"sample {name}"
        else:
            values[name] = f"sample {name}"
    return schema.model_validate(values)


class FakeEmbeddingProvider(EmbeddingProvider):
    async def generate_embedding(self, text: str) -> list[float]:
        # Deterministic small vector so repeated calls in a test are stable.
        seed = sum(bytearray(text.encode("utf-8"))) % 997
        return [((seed + i) % 100) / 100.0 for i in range(settings.EMBEDDING_DIMENSION)]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.generate_embedding(t) for t in texts]


@pytest.fixture
def fake_llm(monkeypatch) -> FakeLLMProvider:
    provider = FakeLLMProvider()
    monkeypatch.setattr(
        "app.services.rag.rag_service.get_llm_provider", lambda: provider
    )
    monkeypatch.setattr("app.services.ai.ai_service.get_llm_provider", lambda: provider)
    return provider


@pytest.fixture
def fake_embeddings(monkeypatch) -> FakeEmbeddingProvider:
    provider = FakeEmbeddingProvider()
    monkeypatch.setattr(
        "app.services.rag.retrieval_service.get_embedding_provider", lambda: provider
    )
    monkeypatch.setattr(
        "app.services.indexing.indexing_service.get_embedding_provider",
        lambda: provider,
    )
    return provider


# ----------------------------------------------------------------------
# Mongo / Redis / Qdrant
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def mongo_db(monkeypatch):
    client = AsyncMongoMockClient()
    db = client["ai_copilot_test"]
    monkeypatch.setattr(mongodb_module, "_client", client)
    monkeypatch.setattr(mongodb_module, "_db", db)
    await db.users.create_index("email", unique=True)
    await db.repositories.create_index([("owner", 1), ("githubUrl", 1)], unique=True)
    yield db


@pytest_asyncio.fixture(autouse=True)
async def redis_fake(monkeypatch):
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_module, "_client", fake_client)
    monkeypatch.setattr(redis_module, "_available", True)
    yield fake_client
    await fake_client.flushall()


@pytest_asyncio.fixture(autouse=True)
async def qdrant_memory(monkeypatch):
    client = AsyncQdrantClient(location=":memory:")
    monkeypatch.setattr(qdrant_module, "_client", client)
    await create_code_collection()
    yield client


# ----------------------------------------------------------------------
# GitHub mocking
# ----------------------------------------------------------------------
SAMPLE_FILES = {
    "src/authController.js": "function login(req, res) {\n  // handles login\n  return res.json({ ok: true });\n}\n",
    "src/userModel.js": "class User {\n  constructor(name) {\n    this.name = name;\n  }\n}\n",
}


def _blob_sha(path: str) -> str:
    return "sha-" + base64.urlsafe_b64encode(path.encode()).decode().rstrip("=")


@pytest.fixture
def github_mock():
    with respx.mock(base_url="https://api.github.com", assert_all_called=False) as mock:
        mock.get(f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "name": GITHUB_REPO,
                    "description": "Sample repository for tests",
                    "private": False,
                    "default_branch": "main",
                },
            )
        )

        tree = [
            {"path": path, "type": "blob", "sha": _blob_sha(path), "size": len(content)}
            for path, content in SAMPLE_FILES.items()
        ]
        mock.get(
            f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/trees/main",
            params={"recursive": "1"},
        ).mock(return_value=httpx.Response(200, json={"tree": tree}))

        for path, content in SAMPLE_FILES.items():
            sha = _blob_sha(path)
            encoded = base64.b64encode(content.encode()).decode()
            mock.get(f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/blobs/{sha}").mock(
                return_value=httpx.Response(
                    200, json={"content": encoded, "encoding": "base64"}
                )
            )

        yield mock


@pytest.fixture
def github_not_found():
    with respx.mock(base_url="https://api.github.com", assert_all_called=False) as mock:
        mock.get(f"/repos/{GITHUB_OWNER}/missing-repo").mock(
            return_value=httpx.Response(404)
        )
        yield mock


# ----------------------------------------------------------------------
# HTTP client
# ----------------------------------------------------------------------
@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_and_login(
    client: httpx.AsyncClient, email: str = "user@example.com"
) -> dict:
    await client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "password123"}
    )
    body = response.json()
    return {"token": body["token"], "user": body["user"]}


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
