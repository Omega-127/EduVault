<<<<<<< HEAD
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
=======
import uuid
from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, Query, WebSocket, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validates the Bearer JWT token from the Authorization header and returns the User."""
    if not authorization:
        raise AuthenticationException("Authorization header is missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException("Invalid authorization header format. Must be 'Bearer <token>'")

    token = parts[1]
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid token payload: missing sub")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationException("Invalid user ID format in token")
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

<<<<<<< HEAD
    if not user or not user.is_active:
        raise CredentialsException("User account not found or disabled")
=======
    if not user:
        raise AuthenticationException("User does not exist")
    if not user.is_active:
        raise AuthenticationException("User account is inactive")
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

    return user


<<<<<<< HEAD
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
=======
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
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user_id = uuid.UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User inactive or not found")
            raise HTTPException(status_code=401, detail="User inactive or not found")

        return user
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
