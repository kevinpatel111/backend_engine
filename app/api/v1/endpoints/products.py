"""Product endpoints: CRUD with pagination, filtering, search, sorting, and ownership protection."""

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.productrepository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.productservice import ProductService
from app.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ProductService:
    product_repo = ProductRepository(session)
    return ProductService(product_repo)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    product_in: ProductCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Creates a new product belonging to the authenticated user."""
    product = await product_service.create_product(product_in, current_user)
    return ProductResponse.model_validate(product)


@router.get(
    "/",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products with filtering, search, pagination, and sorting",
)
async def list_products(
    product_service: Annotated[ProductService, Depends(get_product_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(
        None, description="Search term matching product name or description"
    ),
    sort_by: str = Query(
        "created_at", pattern="^(created_at|price|name|updated_at)$", description="Field to sort by"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
) -> PaginatedResponse[ProductResponse]:
    """Lists products accessible to the current user (user-scoped or all for admins)."""
    owner_filter = None if current_user.role.value == "admin" else current_user.id
    products, total = await product_service.list_products(
        page=page,
        page_size=page_size,
        search=search,
        owner_id=owner_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse[ProductResponse](
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
)
async def get_product_by_id(
    product_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Retrieves product by ID, guaranteeing ownership access rules."""
    product = await product_service.get_by_id(product_id)
    if product.owner_id != current_user.id and current_user.role.value != "admin":
        from app.core.exceptions import ForbiddenException

        raise ForbiddenException("You do not have permission to view this product")
    return ProductResponse.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product by ID",
)
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Updates product attributes (Owner or Admin only)."""
    updated = await product_service.update_product(product_id, product_in, current_user)
    return ProductResponse.model_validate(updated)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product by ID",
)
async def delete_product(
    product_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    """Deletes product (Owner or Admin only)."""
    await product_service.delete_product(product_id, current_user)
