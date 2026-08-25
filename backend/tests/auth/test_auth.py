import pytest

from tests.conftest import auth_headers, register_and_login


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/api/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["user"]["email"] == "alice@example.com"
    assert "password" not in body["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"name": "Alice", "email": "dup@example.com", "password": "password123"}
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["success"] is False


@pytest.mark.asyncio
async def test_register_invalid_input(client):
    response = await client.post(
        "/api/auth/register",
        json={"name": "", "email": "not-an-email", "password": "123"},
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": "bob@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "token" in body


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={"name": "Carl", "email": "carl@example.com", "password": "password123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "carl@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_profile_unauthorized_without_token(client):
    response = await client.get("/api/auth/profile")
    assert response.status_code == 401
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_profile_authorized(client):
    session = await register_and_login(client, "dana@example.com")
    response = await client.get(
        "/api/auth/profile", headers=auth_headers(session["token"])
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "dana@example.com"


@pytest.mark.asyncio
async def test_profile_rejects_invalid_token(client):
    response = await client.get(
        "/api/auth/profile", headers=auth_headers("not-a-real-token")
    )
    assert response.status_code == 401
