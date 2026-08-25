import asyncio

import pytest

from app.models import repository as repository_model
from tests.conftest import GITHUB_URL, auth_headers, register_and_login


async def _create_repo(client, headers) -> str:
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    return created.json()["repository"]["id"]


@pytest.mark.asyncio
async def test_start_indexing_success(client, github_mock, fake_embeddings):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_repo(client, headers)

    response = await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "indexing"

    # Allow the background asyncio task to run to completion.
    await asyncio.sleep(0.5)

    repo_doc = await repository_model.find_repository_by_id(repo_id)
    assert repo_doc["indexingStatus"] == "ready"
    assert repo_doc["activeIndexVersion"] is not None
    assert repo_doc["indexedChunks"] > 0


@pytest.mark.asyncio
async def test_start_indexing_duplicate_while_running(
    client, github_mock, fake_embeddings
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_repo(client, headers)

    first = await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    assert first.status_code == 202

    second = await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    assert second.status_code == 409

    await asyncio.sleep(0.5)


@pytest.mark.asyncio
async def test_index_status_reports_progress(client, github_mock, fake_embeddings):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_repo(client, headers)

    await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    await asyncio.sleep(0.5)

    response = await client.get(
        f"/api/repositories/{repo_id}/index-status", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["ready"] is True
    assert body["progress"] == 100


@pytest.mark.asyncio
async def test_index_invalid_repository(client):
    session = await register_and_login(client)
    response = await client.post(
        "/api/repositories/64b1f0c2e1b1c2d3e4f56789/index",
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_indexing_failure_is_recorded(
    client, github_not_found, fake_embeddings, monkeypatch
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])

    # Create the repository against the *working* mock first via a direct model call,
    # since creation requires a successful GitHub metadata fetch.
    import httpx
    import respx

    with respx.mock(base_url="https://api.github.com", assert_all_called=False) as mock:
        mock.get("/repos/octocat/hello-world").mock(
            return_value=httpx.Response(
                200,
                json={
                    "name": "hello-world",
                    "description": "",
                    "private": False,
                    "default_branch": "main",
                },
            )
        )
        created = await client.post(
            "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
        )
    repo_id = created.json()["repository"]["id"]

    # Now indexing runs against a GitHub mock that 404s on the tree fetch, so the
    # background job should fail gracefully and record the error.
    with respx.mock(base_url="https://api.github.com", assert_all_called=False) as mock:
        mock.get(
            "/repos/octocat/hello-world/git/trees/main", params={"recursive": "1"}
        ).mock(return_value=httpx.Response(404))

        response = await client.post(
            f"/api/repositories/{repo_id}/index", headers=headers
        )
        assert response.status_code == 202
        await asyncio.sleep(0.5)

    repo_doc = await repository_model.find_repository_by_id(repo_id)
    assert repo_doc["indexingStatus"] == "failed"
    assert repo_doc["indexingError"] is not None
