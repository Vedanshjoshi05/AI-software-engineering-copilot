import asyncio

import pytest

from tests.conftest import GITHUB_URL, auth_headers, register_and_login


async def _create_and_index_repo(client, headers, github_mock, fake_embeddings) -> str:
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]
    await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    await asyncio.sleep(0.5)
    return repo_id


@pytest.mark.asyncio
async def test_ask_unauthorized(client):
    response = await client.post(
        "/api/repositories/64b1f0c2e1b1c2d3e4f56789/ask",
        json={"question": "What does this do?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_missing_question(client, github_mock, fake_embeddings):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/ask", json={}, headers=headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ask_invalid_repository(client):
    session = await register_and_login(client)
    response = await client.post(
        "/api/repositories/64b1f0c2e1b1c2d3e4f56789/ask",
        json={"question": "What does this do?"},
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ask_not_indexed(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]

    response = await client.post(
        f"/api/repositories/{repo_id}/ask",
        json={"question": "What does this do?"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_ask_returns_answer_and_sources(
    client, github_mock, fake_embeddings, fake_llm
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.generate_response = (
        "The login function authenticates a user and returns JSON."
    )
    response = await client.post(
        f"/api/repositories/{repo_id}/ask",
        json={"question": "How does login work?"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == fake_llm.generate_response
    assert len(body["sources"]) > 0
    assert "path" in body["sources"][0]


@pytest.mark.asyncio
async def test_ask_ownership_enforced(client, github_mock, fake_embeddings):
    owner_session = await register_and_login(client, "owner2@example.com")
    other_session = await register_and_login(client, "other2@example.com")
    repo_id = await _create_and_index_repo(
        client, auth_headers(owner_session["token"]), github_mock, fake_embeddings
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/ask",
        json={"question": "How does login work?"},
        headers=auth_headers(other_session["token"]),
    )
    assert response.status_code == 404
