"""Unit tests for AuthService: registration, authentication, token hashing, and refresh handling."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import get_password_hash, verify_password
from app.models.user import UserRole
from app.repositories.userrepository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.authservice import AuthService


@pytest.mark.asyncio
async def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


@pytest.mark.asyncio
async def test_auth_service_register(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    user_in = UserCreate(
        email="newuser@example.com",
        full_name="New Registered User",
        password="SuperSecurePassword123!",
    )
    user = await auth_service.register(user_in)
    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.role == UserRole.USER
    assert verify_password("SuperSecurePassword123!", user.hashed_password) is True

    # Duplicate registration should raise ConflictException
    with pytest.raises(ConflictException):
        await auth_service.register(user_in)


@pytest.mark.asyncio
async def test_auth_service_authenticate(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo)

    user_in = UserCreate(
        email="loginuser@example.com",
        full_name="Login Test",
        password="Password123!",
    )
    await auth_service.register(user_in)

    # Valid login
    token = await auth_service.authenticate(
        LoginRequest(email="loginuser@example.com", password="Password123!")
    )
    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "bearer"

    # Invalid password
    with pytest.raises(UnauthorizedException):
        await auth_service.authenticate(
            LoginRequest(email="loginuser@example.com", password="WrongPassword")
        )

    # Non-existent email
    with pytest.raises(UnauthorizedException):
        await auth_service.authenticate(
            LoginRequest(email="nonexistent@example.com", password="Password123!")
        )
