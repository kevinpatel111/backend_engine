"""Role-based access control and permission dependencies."""

from typing import Annotated

from fastapi import Depends

from app.core.exceptions import ForbiddenException
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException("Operation not permitted for current user role")
        return current_user


require_admin = RoleChecker([UserRole.ADMIN])
require_user_or_admin = RoleChecker([UserRole.USER, UserRole.ADMIN])
