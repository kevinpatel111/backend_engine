"""User repository handling database operations for User and RefreshToken entities."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        query = select(User)
        count_query = select(func.count(User.id))

        if search:
            search_filter = (User.full_name.ilike(f"%{search}%")) | (
                User.email.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Ordering
        column = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

        total_res = await self.session.execute(count_query)
        total = total_res.scalar_one()

        query = query.offset(skip).limit(limit)
        items_res = await self.session.execute(query)
        return list(items_res.scalars().all()), total

    # RefreshToken management
    async def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_refresh_token(self, token_id: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_id == token_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked = True
        await self.session.commit()
