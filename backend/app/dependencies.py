from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.core.exceptions import CredentialsException, PermissionDeniedException
from app.db.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise CredentialsException("Authentication token required")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise CredentialsException("Invalid or expired token")

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise CredentialsException("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CredentialsException("User account not found or disabled")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise PermissionDeniedException("Administrator role required")
    return current_user


async def get_user_from_token_string(token: str, db: AsyncSession) -> Optional[User]:
    """Used for WebSocket query parameter authentication."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        return user
    return None
