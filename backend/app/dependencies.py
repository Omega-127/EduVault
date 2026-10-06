import uuid
from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, Query, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validates the Bearer JWT token from Authorization header or query parameter and returns the User."""
    jwt_token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            jwt_token = parts[1]
        else:
            raise AuthenticationException("Invalid authorization header format. Must be 'Bearer <token>'")
    elif token:
        jwt_token = token
    else:
        raise AuthenticationException("Authorization header is missing")
    payload = decode_token(jwt_token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid token payload: missing sub")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationException("Invalid user ID format in token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationException("User does not exist")
    if not user.is_active:
        raise AuthenticationException("User account is inactive")

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures that the authenticated user possesses the 'admin' role."""
    if current_user.role != "admin":
        raise AuthorizationException("Insufficient permissions: Admin role required")
    return current_user


async def get_ws_current_user(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticates a WebSocket connection using a JWT token provided in query parameters."""
    if not token:
        raise AuthenticationException("Missing authentication token")

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationException("Invalid token payload")

        user_id = uuid.UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationException("User inactive or not found")

        return user
    except AuthenticationException:
        raise
    except Exception as e:
        raise AuthenticationException(f"Authentication failed: {str(e)}") from e
