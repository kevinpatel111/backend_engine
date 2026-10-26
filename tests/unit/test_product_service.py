"""Unit tests for ProductService: CRUD, ownership checks, and permissions."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User
from app.repositories.productrepository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.productservice import ProductService


@pytest.mark.asyncio
async def test_product_service_crud_and_ownership(
    db_session: AsyncSession,
    normal_user: User,
    other_user: User,
    admin_user: User,
):
    product_repo = ProductRepository(db_session)
    product_service = ProductService(product_repo)

    # 1. Create product
    product_in = ProductCreate(
        name="Laptop Pro",
        description="High performance laptop",
        price=Decimal("1299.99"),
    )
    product = await product_service.create_product(product_in, normal_user)
    assert product.id is not None
    assert product.name == "Laptop Pro"
    assert product.owner_id == normal_user.id

    # 2. Get by ID
    fetched = await product_service.get_by_id(product.id)
    assert fetched.id == product.id

    # 3. Unauthorized update attempt by other user should raise ForbiddenException
    update_in = ProductUpdate(name="Hacked Laptop")
    with pytest.raises(ForbiddenException):
        await product_service.update_product(product.id, update_in, other_user)

    # 4. Authorized update by owner
    valid_update = ProductUpdate(name="Updated Laptop Pro", price=Decimal("1199.50"))
    updated = await product_service.update_product(product.id, valid_update, normal_user)
    assert updated.name == "Updated Laptop Pro"
    assert updated.price == Decimal("1199.50")

    # 5. Admin can update any product
    admin_update = ProductUpdate(description="Admin reviewed")
    admin_res = await product_service.update_product(product.id, admin_update, admin_user)
    assert admin_res.description == "Admin reviewed"

    # 6. Unauthorized delete by another user
    with pytest.raises(ForbiddenException):
        await product_service.delete_product(product.id, other_user)

    # 7. Authorized delete by owner
    await product_service.delete_product(product.id, normal_user)

    # 8. Fetching deleted item raises NotFoundException
    with pytest.raises(NotFoundException):
        await product_service.get_by_id(product.id)
