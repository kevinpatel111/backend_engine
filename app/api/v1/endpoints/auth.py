"""Authentication endpoints: register, login, refresh, logout."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.userrepository import UserRepository
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.authservice import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    user_repo = UserRepository(session)
    return AuthService(user_repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Creates a new user profile with hashed password credentials."""
    user = await auth_service.register(user_in)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain access & refresh tokens",
)
async def login(
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Authenticates credentials and returns access and refresh tokens."""
    return await auth_service.authenticate(login_data)


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Rotate tokens using a valid refresh token",
)
async def refresh_tokens(
    refresh_data: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Rotates refresh token and returns a newly generated token pair."""
    return await auth_service.refresh_tokens(refresh_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token on logout",
)
async def logout(
    logout_data: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Invalidates the provided refresh token in the database."""
    await auth_service.logout(logout_data.refresh_token)
