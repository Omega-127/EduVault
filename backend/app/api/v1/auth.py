from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationException
from app.db.session import get_db
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new student, faculty, or admin user."""
    user = await AuthService.register_user(db, request)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT access & refresh tokens",
)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates user credentials and sets an HTTP-only cookie with the refresh token."""
    user, access_token, refresh_token = await AuthService.authenticate_user(db, request)

    # Set secure HTTP-only refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        samesite="lax",
        secure=settings.APP_ENV == "production",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate JWT access token using HTTP-only refresh cookie",
)
async def refresh_token(
    refresh_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Rotates the access token using the HTTP-only refresh token cookie."""
    if not refresh_token:
        raise AuthenticationException("Refresh token cookie is missing")

    user, access_token = await AuthService.refresh_access_token(db, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
