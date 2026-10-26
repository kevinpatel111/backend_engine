"""User profile and administrative management endpoints."""

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.repositories.userrepository import UserRepository
from app.schemas.user import UserAdminUpdate, UserResponse, UserUpdate
from app.services.userservice import UserService
from app.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    user_repo = UserRepository(session)
    return UserService(user_repo)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Returns details for the currently logged-in user."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current authenticated user profile",
)
async def update_current_user_profile(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Updates non-administrative fields for current authenticated user."""
    updated = await user_service.update_user(current_user.id, user_in, current_user)
    return UserResponse.model_validate(updated)


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users (Admin only)",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by full name or email"),
    sort_by: str = Query("created_at", pattern="^(created_at|full_name|email)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[UserResponse]:
    """Admin-only endpoint to search and paginate all users."""
    users, total = await user_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse[UserResponse](
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Retrieves user profile details (enforces role or self-access authorization)."""
    # Authorized if admin or self
    if current_user.role.value != "admin" and current_user.id != user_id:
        from app.core.exceptions import ForbiddenException

        raise ForbiddenException("Access denied to requested profile")

    user = await user_service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user by ID",
)
async def update_user_by_id(
    user_id: uuid.UUID,
    user_in: UserAdminUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Updates user fields according to role and ownership privileges."""
    updated = await user_service.update_user(user_id, user_in, current_user)
    return UserResponse.model_validate(updated)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
)
async def delete_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Deletes user account (Admin or account owner only)."""
    await user_service.delete_user(user_id, current_user)
