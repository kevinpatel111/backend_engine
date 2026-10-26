"""User service handling account profiles, role modifications, and authorization rules."""

import uuid

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories.userrepository import UserRepository
from app.schemas.user import UserAdminUpdate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        skip = (page - 1) * page_size
        return await self.user_repo.list_users(
            skip=skip,
            limit=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update_user(
        self,
        user_id: uuid.UUID,
        user_in: UserUpdate | UserAdminUpdate,
        current_user: User,
    ) -> User:
        user = await self.get_by_id(user_id)

        # Check permissions: only admin or the user themselves can update
        is_owner = current_user.id == user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_owner or is_admin):
            raise ForbiddenException("You do not have permission to update this profile")

        # Check email uniqueness if changing email
        if user_in.email and user_in.email != user.email:
            existing = await self.user_repo.get_by_email(user_in.email)
            if existing and existing.id != user.id:
                raise ConflictException("Email already in use by another account")
            user.email = user_in.email.lower().strip()

        if user_in.full_name is not None:
            user.full_name = user_in.full_name.strip()

        if user_in.password:
            user.hashed_password = get_password_hash(user_in.password)

        # Handle admin-only privileged fields
        if isinstance(user_in, UserAdminUpdate):
            if not is_admin:
                if user_in.role is not None or user_in.is_active is not None:
                    raise ForbiddenException("Only administrators can update roles or status")
            else:
                if user_in.role is not None:
                    user.role = user_in.role
                if user_in.is_active is not None:
                    user.is_active = user_in.is_active

        return await self.user_repo.update(user)

    async def delete_user(self, user_id: uuid.UUID, current_user: User) -> None:
        user = await self.get_by_id(user_id)

        # Only admin or self-deletion allowed
        if current_user.role != UserRole.ADMIN and current_user.id != user.id:
            raise ForbiddenException("You do not have permission to delete this account")

        await self.user_repo.delete(user)
