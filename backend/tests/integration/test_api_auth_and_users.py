"""API tests for /auth and /users using real HTTP requests to verify routing, dependencies, and error handling."""

import uuid

import pytest


def _unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@fraudshield.ai"


@pytest.mark.asyncio
async def test_register_returns_201_and_user_shape(api_client, clean_api_tables):
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": _unique_email("reg"),
            "password": "Password1",
            "full_name": "API Test User",
            "role": "analyst",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "analyst"
    assert body["is_active"] is True
    assert "id" in body
    assert "hashed_password" not in body  # never leaked in the response


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(api_client, clean_api_tables):
    email = _unique_email("dup")
    payload = {"email": email, "password": "Password1", "full_name": "Dup", "role": "analyst"}

    first = await api_client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await api_client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"] == "conflict"


@pytest.mark.asyncio
async def test_register_weak_password_returns_422(api_client, clean_api_tables):
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email("weak"), "password": "weak", "full_name": "Weak", "role": "analyst"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_with_correct_credentials_returns_token_pair(api_client, clean_api_tables):
    email = _unique_email("login")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Login Test", "role": "analyst"},
    )

    response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(api_client, clean_api_tables):
    email = _unique_email("wrongpw")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Wrong PW", "role": "analyst"},
    )

    response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "WrongPassword1"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_and_logout_flow(api_client, clean_api_tables):
    email = _unique_email("refresh")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Refresh Test", "role": "analyst"},
    )
    login_resp = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password1"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    logout_resp = await api_client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    # the same refresh token must be rejected after logout
    reuse_resp = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401


@pytest.mark.asyncio
async def test_users_me_requires_authentication(api_client, clean_api_tables):
    response = await api_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_users_me_returns_current_user(api_client, clean_api_tables):
    email = _unique_email("me")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Me Test", "role": "analyst"},
    )
    login_resp = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password1"}
    )
    token = login_resp.json()["access_token"]

    response = await api_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == email


@pytest.mark.asyncio
async def test_analyst_cannot_list_users_admin_only_route(api_client, clean_api_tables):
    email = _unique_email("analyst")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Analyst", "role": "analyst"},
    )
    login_resp = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password1"}
    )
    token = login_resp.json()["access_token"]

    response = await api_client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(api_client, clean_api_tables):
    email = _unique_email("admin")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Admin", "role": "admin"},
    )
    login_resp = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password1"}
    )
    token = login_resp.json()["access_token"]

    response = await api_client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_can_deactivate_and_reactivate_a_user(api_client, clean_api_tables):
    admin_email = _unique_email("admin2")
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "Password1", "full_name": "Admin2", "role": "admin"},
    )
    admin_token = (
        await api_client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password1"})
    ).json()["access_token"]

    target_email = _unique_email("target")
    target_resp = await api_client.post(
        "/api/v1/auth/register",
        json={"email": target_email, "password": "Password1", "full_name": "Target", "role": "analyst"},
    )
    target_id = target_resp.json()["id"]

    deactivate_resp = await api_client.post(
        f"/api/v1/users/{target_id}/deactivate", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    reactivate_resp = await api_client.post(
        f"/api/v1/users/{target_id}/reactivate", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["is_active"] is True
