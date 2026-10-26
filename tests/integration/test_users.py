"""Integration tests for User endpoints (/api/v1/users)."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_users_endpoints(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
    admin_user: User,
):
    user_token = create_access_token(str(normal_user.id), "user")
    admin_token = create_access_token(str(admin_user.id), "admin")

    # 1. /users/me
    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == normal_user.email

    # 2. Update /users/me
    patch_me = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Regular Name"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert patch_me.status_code == 200
    assert patch_me.json()["full_name"] == "Updated Regular Name"

    # 3. Regular user listing all users -> 403 Forbidden
    list_user = await client.get(
        "/api/v1/users/", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert list_user.status_code == 403

    # 4. Admin listing all users -> 200 OK
    list_admin = await client.get(
        "/api/v1/users/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_admin.status_code == 200
    assert list_admin.json()["total"] >= 3

    # 5. Accessing other user's profile with regular user token -> 403 Forbidden
    cross_user = await client.get(
        f"/api/v1/users/{other_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert cross_user.status_code == 403

    # 6. Admin accessing any user profile -> 200 OK
    admin_get_user = await client.get(
        f"/api/v1/users/{other_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_get_user.status_code == 200
    assert admin_get_user.json()["email"] == other_user.email

    # 7. Mass-assignment / privilege escalation protection: regular user trying to elevate to admin
    patch_role = await client.patch(
        f"/api/v1/users/{normal_user.id}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert patch_role.status_code == 403

    # 8. Admin deleting user
    delete_resp = await client.delete(
        f"/api/v1/users/{other_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_resp.status_code == 204
