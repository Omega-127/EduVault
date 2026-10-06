from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies import get_current_user, get_ws_current_user
from app.schemas.chat import (
    ChatAskResponse,
    ChatQuestionRequest,
    CreateSessionRequest,
    MessageResponse,
    SessionResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_session(
    request: Optional[CreateSessionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new chat session owned by the authenticated user."""
    session = await ChatService.create_session(db, current_user, request)
    return SessionResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="List all chat sessions for the current user",
)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all chat sessions for the logged-in user in descending order of update."""
    sessions = await ChatService.list_sessions(db, current_user)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get chat session details",
)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves session metadata if the current user owns it."""
    session = await ChatService.get_session(db, session_id, current_user)
    return SessionResponse.model_validate(session)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[MessageResponse],
    summary="Get full message history for a chat session",
)
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves message history for the specified session."""
    messages = await ChatService.get_session_messages(db, session_id, current_user)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/sessions/{session_id}/ask",
    response_model=ChatAskResponse,
    summary="Ask a question and receive a grounded answer (HTTP)",
)
async def ask_question(
    session_id: uuid.UUID,
    request: ChatQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """HTTP alternative to the WebSocket stream — more reliable through proxies and free-tier hosts."""
    user_msg, asst_msg = await ChatService.answer_question(
        db, session_id, current_user, request.question
    )
    return ChatAskResponse(
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(asst_msg),
    )


@router.websocket("/sessions/{session_id}/stream")
async def chat_stream_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket streaming endpoint for real-time grounded Q&A with token and citation frames."""
    # Accept first so auth failures can close cleanly (closing before accept breaks ASGI)
    await websocket.accept()

    try:
        user = await get_ws_current_user(websocket, token=token, db=db)
    except Exception:
        try:
            await websocket.send_json(
                {"type": "error", "data": "Authentication failed. Please log in again."}
            )
        except Exception:
            pass
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        await ChatService.handle_stream(websocket, session_id, user, db)
    except WebSocketDisconnect:
        pass
