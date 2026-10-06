import uuid
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, DuplicateResourceException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


class AuthService:
    """Service handling user registration, authentication, and token issuance."""

    @staticmethod
    async def register_user(db: AsyncSession, request: UserRegisterRequest) -> User:
        result = await db.execute(select(User).where(User.email == request.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise DuplicateResourceException("A user with this email address already exists")

        new_user = User(
            email=request.email,
            hashed_pw=get_password_hash(request.password),
            role=request.role or "student",
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, request: UserLoginRequest) -> Tuple[User, str, str]:
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_pw):
            raise AuthenticationException("Invalid email or password")

        if not user.is_active:
            raise AuthenticationException("User account is inactive")

        token_payload = {
            "sub": str(user.id),
            "role": user.role,
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        return user, access_token, refresh_token

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Tuple[User, str]:
        if not refresh_token:
            raise AuthenticationException("Refresh token is required")

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid token type: expected refresh token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationException("Invalid refresh token payload")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise AuthenticationException("Invalid user ID in refresh token")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive")

        token_payload = {
            "sub": str(user.id),
            "role": user.role,
        }
        new_access_token = create_access_token(token_payload)
        return user, new_access_token
