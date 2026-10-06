<<<<<<< HEAD
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
=======
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
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

router = APIRouter(prefix="/auth", tags=["Authentication"])


<<<<<<< HEAD
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "student"


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def set_refresh_cookie(response: Response, refresh_token: str):
=======
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
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
<<<<<<< HEAD
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )


@router.post("/register", response_model=AuthResponse)
async def register(
    data: RegisterSchema,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role if data.role in ("student", "faculty", "admin") else "student",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id, "role": user.role})
    set_refresh_cookie(response, refresh_token)

    return AuthResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id, "role": user.role})
    set_refresh_cookie(response, refresh_token)

    return AuthResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token({"sub": user.id, "role": user.role})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}
=======
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
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
