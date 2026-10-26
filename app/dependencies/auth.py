"""FastAPI dependencies for JWT authentication and current user injection."""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.userrepository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True,
)


async def get_user_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError as err:
        raise UnauthorizedException("Access token has expired") from err
    except jwt.PyJWTError as err:
        raise UnauthorizedException("Could not validate credentials") from err

    token_type = payload.get("type")
    sub = payload.get("sub")

    if token_type != "access" or not sub:
        raise UnauthorizedException("Invalid token type or missing subject")

    try:
        user_uuid = uuid.UUID(sub)
    except ValueError as err:
        raise UnauthorizedException("Invalid user identity") from err

    user = await user_repo.get_by_id(user_uuid)
    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("Inactive user account")

    return user
