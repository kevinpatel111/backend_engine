"""Integration tests for Product endpoints: CRUD, pagination, filtering, ownership."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_products_full_lifecycle(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
    admin_user: User,
):
    user_token = create_access_token(str(normal_user.id), "user")
    other_token = create_access_token(str(other_user.id), "user")

    # 1. Create product without token -> 401
    unauth_resp = await client.post(
        "/api/v1/products/",
        json={"name": "Widget", "price": 49.99},
    )
    assert unauth_resp.status_code == 401

    # 2. Validation failure: negative price -> 422
    val_err = await client.post(
        "/api/v1/products/",
        json={"name": "Widget", "price": -10.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert val_err.status_code == 422

    # 3. Create product
    prod_data = {
        "name": "Wireless Mechanical Keyboard",
        "description": "Ergonomic keyboard with Bluetooth",
        "price": 149.99,
    }
    create_resp = await client.post(
        "/api/v1/products/",
        json=prod_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert create_resp.status_code == 201
    prod = create_resp.json()
    product_id = prod["id"]
    assert prod["name"] == "Wireless Mechanical Keyboard"
    assert prod["owner_id"] == str(normal_user.id)

    # 4. List products - test search & pagination
    list_resp = await client.get(
        "/api/v1/products/?search=Keyboard&page=1&page_size=10&sort_by=price&sort_order=desc",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == product_id

    # 5. Other user should not see normal_user's product in list
    other_list = await client.get(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0

    # 6. Other user accessing product directly by ID -> 403 Forbidden
    cross_access = await client.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_access.status_code == 403

    # 7. Other user trying to patch product -> 403 Forbidden
    cross_patch = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Tampered Name"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_patch.status_code == 403

    # 8. Owner updating product
    patch_resp = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"price": 129.99},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert patch_resp.status_code == 200
    assert float(patch_resp.json()["price"]) == 129.99

    # 9. Non-existent product -> 404
    fake_id = uuid.uuid4()
    not_found = await client.get(
        f"/api/v1/products/{fake_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert not_found.status_code == 404

    # 10. Owner deleting product -> 204
    delete_resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert delete_resp.status_code == 204

    # 11. Verify deleted -> 404
    get_del = await client.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert get_del.status_code == 404
