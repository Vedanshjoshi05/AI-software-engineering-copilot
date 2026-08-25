import pytest

from tests.conftest import GITHUB_URL, auth_headers, register_and_login


@pytest.mark.asyncio
async def test_create_repository_success(client, github_mock):
    session = await register_and_login(client)
    response = await client.post(
        "/api/repositories",
        json={"githubUrl": GITHUB_URL},
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["repository"]["githubUrl"] == GITHUB_URL
    assert body["repository"]["indexingStatus"] == "not_indexed"


@pytest.mark.asyncio
async def test_create_repository_duplicate(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])

    first = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    assert second.status_code == 409
    assert second.json()["success"] is False


@pytest.mark.asyncio
async def test_create_repository_invalid_url(client):
    session = await register_and_login(client)
    response = await client.post(
        "/api/repositories",
        json={"githubUrl": "not-a-github-url"},
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_repository_not_found_on_github(client, github_not_found):
    session = await register_and_login(client)
    response = await client.post(
        "/api/repositories",
        json={"githubUrl": "https://github.com/octocat/missing-repo"},
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_repositories(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )

    response = await client.get("/api/repositories", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert len(body["repositories"]) == 1


@pytest.mark.asyncio
async def test_get_repository(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]

    response = await client.get(f"/api/repositories/{repo_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["repository"]["id"] == repo_id


@pytest.mark.asyncio
async def test_get_repository_not_found(client):
    session = await register_and_login(client)
    response = await client.get(
        "/api/repositories/64b1f0c2e1b1c2d3e4f56789",
        headers=auth_headers(session["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_repository(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]

    response = await client.delete(f"/api/repositories/{repo_id}", headers=headers)
    assert response.status_code == 200

    follow_up = await client.get(f"/api/repositories/{repo_id}", headers=headers)
    assert follow_up.status_code == 404


@pytest.mark.asyncio
async def test_repository_ownership_enforced(client, github_mock):
    owner_session = await register_and_login(client, "owner@example.com")
    other_session = await register_and_login(client, "other@example.com")

    created = await client.post(
        "/api/repositories",
        json={"githubUrl": GITHUB_URL},
        headers=auth_headers(owner_session["token"]),
    )
    repo_id = created.json()["repository"]["id"]

    # Other user cannot see, delete, or otherwise access this repository.
    get_response = await client.get(
        f"/api/repositories/{repo_id}", headers=auth_headers(other_session["token"])
    )
    assert get_response.status_code == 404

    delete_response = await client.delete(
        f"/api/repositories/{repo_id}", headers=auth_headers(other_session["token"])
    )
    assert delete_response.status_code == 404
