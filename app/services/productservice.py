"""Product service coordinating product business rules, ownership checks, and search/pagination."""

import uuid

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.product import Product
from app.models.user import User, UserRole
from app.repositories.productrepository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, product_repo: ProductRepository) -> None:
        self.product_repo = product_repo

    async def get_by_id(self, product_id: uuid.UUID) -> Product:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Product not found")
        return product

    async def create_product(self, product_in: ProductCreate, owner: User) -> Product:
        product = Product(
            name=product_in.name.strip(),
            description=product_in.description.strip() if product_in.description else None,
            price=product_in.price,
            owner_id=owner.id,
        )
        return await self.product_repo.create(product)

    async def update_product(
        self,
        product_id: uuid.UUID,
        product_in: ProductUpdate,
        current_user: User,
    ) -> Product:
        product = await self.get_by_id(product_id)

        # Enforce resource ownership (or admin privileges)
        if product.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to modify this product")

        if product_in.name is not None:
            product.name = product_in.name.strip()
        if product_in.description is not None:
            product.description = product_in.description.strip()
        if product_in.price is not None:
            product.price = product_in.price

        return await self.product_repo.update(product)

    async def delete_product(self, product_id: uuid.UUID, current_user: User) -> None:
        product = await self.get_by_id(product_id)

        # Enforce resource ownership (or admin privileges)
        if product.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to delete this product")

        await self.product_repo.delete(product)

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        owner_id: uuid.UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        skip = (page - 1) * page_size
        return await self.product_repo.list_products(
            skip=skip,
            limit=page_size,
            search=search,
            owner_id=owner_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )
