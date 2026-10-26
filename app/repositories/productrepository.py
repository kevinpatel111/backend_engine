"""Product repository handling database persistence and scoped queries for Products."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update(self, product: Product) -> Product:
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.session.delete(product)
        await self.session.commit()

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        owner_id: uuid.UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        query = select(Product)
        count_query = select(func.count(Product.id))

        if owner_id:
            query = query.where(Product.owner_id == owner_id)
            count_query = count_query.where(Product.owner_id == owner_id)

        if search:
            search_filter = (Product.name.ilike(f"%{search}%")) | (
                Product.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        allowed_sort_fields = {"created_at", "price", "name", "updated_at"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        column = getattr(Product, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

        total_res = await self.session.execute(count_query)
        total = total_res.scalar_one()

        query = query.offset(skip).limit(limit)
        items_res = await self.session.execute(query)
        return list(items_res.scalars().all()), total
