"""Auth service orchestrating credentials, tokens, and refresh sessions."""

import uuid
from datetime import UTC, datetime

import jwt

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import RefreshToken, User, UserRole
from app.repositories.userrepository import UserRepository
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate, default_role: UserRole = UserRole.USER) -> User:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise ConflictException("A user with this email address already exists")

        hashed_password = get_password_hash(user_in.password)
        user = User(
            email=user_in.email.lower().strip(),
            full_name=user_in.full_name.strip(),
            hashed_password=hashed_password,
            role=default_role,
            is_active=True,
        )
        return await self.user_repo.create(user)

    async def authenticate(self, login_data: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive")

        return await self._generate_tokens_for_user(user)

    async def refresh_tokens(self, refresh_token_str: str) -> Token:
        try:
            payload = decode_token(refresh_token_str)
        except jwt.PyJWTError as err:
            raise UnauthorizedException("Invalid or expired refresh token") from err

        token_type = payload.get("type")
        sub = payload.get("sub")
        jti = payload.get("jti")

        if token_type != "refresh" or not sub or not jti:
            raise UnauthorizedException("Invalid refresh token structure")

        token_record = await self.user_repo.get_refresh_token(jti)
        if not token_record or token_record.revoked:
            raise UnauthorizedException("Refresh token revoked or not found")

        # Check expiration
        now = datetime.now(UTC)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < now:
            await self.user_repo.revoke_refresh_token(token_record)
            raise UnauthorizedException("Refresh token has expired")

        # Invalidate old refresh token (Token Rotation)
        await self.user_repo.revoke_refresh_token(token_record)

        user = await self.user_repo.get_by_id(uuid.UUID(sub))
        if not user or not user.is_active:
            raise UnauthorizedException("User inactive or no longer exists")

        # Issue new token pair
        return await self._generate_tokens_for_user(user)

    async def logout(self, refresh_token_str: str) -> None:
        try:
            payload = decode_token(refresh_token_str)
            jti = payload.get("jti")
            if jti:
                token_record = await self.user_repo.get_refresh_token(jti)
                if token_record:
                    await self.user_repo.revoke_refresh_token(token_record)
        except Exception:
            # Idempotent logout - discard errors
            pass

    async def _generate_tokens_for_user(self, user: User) -> Token:
        access_token = create_access_token(str(user.id), user.role.value)
        jti = str(uuid.uuid4())
        refresh_token = create_refresh_token(str(user.id), jti)

        # Store refresh token record in DB for revocation tracking
        now = datetime.now(UTC)
        expires_at = now + (settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60) * (
            datetime.fromtimestamp(1, UTC) - datetime.fromtimestamp(0, UTC)
        )
        token_record = RefreshToken(
            token_id=jti,
            user_id=user.id,
            revoked=False,
            expires_at=expires_at,
        )
        await self.user_repo.create_refresh_token(token_record)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
