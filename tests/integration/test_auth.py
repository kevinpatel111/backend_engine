"""Integration tests for Authentication endpoints (/api/v1/auth)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "email": "flow_user@example.com",
        "full_name": "Integration User",
        "password": "Password123!",
    }
    resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "flow_user@example.com"
    assert data["role"] == "user"
    assert "hashed_password" not in data

    # 2. Duplicate registration conflict (409)
    dup_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 409

    # 3. Login with invalid password (401)
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "flow_user@example.com", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 4. Successful login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "flow_user@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Access protected /users/me endpoint
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "flow_user@example.com"

    # 6. Refresh tokens
    ref_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_resp.status_code == 200
    new_tokens = ref_resp.json()
    new_refresh = new_tokens["refresh_token"]

    # Old refresh token should be revoked (rotation)
    old_ref_try = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert old_ref_try.status_code == 401

    # 7. Logout with new refresh token
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout_resp.status_code == 204

    # Using revoked refresh token after logout should fail (401)
    revoked_try = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert revoked_try.status_code == 401
