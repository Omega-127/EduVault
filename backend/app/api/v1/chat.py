<<<<<<< HEAD
import json
from datetime import datetime
from typing import List, Optional, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
    Query,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies import get_db, get_current_user, get_user_from_token_string
from app.db.session import AsyncSessionLocal
from app.db.models.chat_session import ChatSession
from app.db.models.message import Message
from app.db.models.user import User
from app.services.rag_service import rag_service
=======
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies import get_current_user, get_ws_current_user
from app.schemas.chat import (
    CreateSessionRequest,
    MessageResponse,
    SessionResponse,
)
from app.services.chat_service import ChatService
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

router = APIRouter(prefix="/chat", tags=["Chat"])


<<<<<<< HEAD
class CitationSchema(BaseModel):
    document_name: str
    page: Optional[int] = 1
    section: Optional[str] = "General"
    chunk_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: List[CitationSchema] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateSessionSchema(BaseModel):
    title: Optional[str] = "New Chat"


@router.get("/sessions", response_model=List[ChatSessionResponse])
=======
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
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
<<<<<<< HEAD
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    data: CreateSessionSchema = CreateSessionSchema(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(
        user_id=current_user.id,
        title=data.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    await db.delete(session)
    await db.commit()
    return {"message": "Chat session deleted"}


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    response_list = []
    for msg in messages:
        try:
            parsed_citations = json.loads(msg.citations) if msg.citations else []
        except Exception:
            parsed_citations = []

        response_list.append(
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                citations=parsed_citations,
                created_at=msg.created_at,
            )
        )
    return response_list


@router.websocket("/sessions/{session_id}/stream")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
):
    await websocket.accept()

    if not token:
        await websocket.send_json({"type": "error", "data": "Authentication token missing"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        user = await get_user_from_token_string(token, db)
        if not user:
            await websocket.send_json({"type": "error", "data": "Unauthorized token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            session = ChatSession(id=session_id, user_id=user.id, title="New Chat")
            db.add(session)
            await db.commit()

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                payload = json.loads(raw_text)
                question = payload.get("question", "").strip()
            except Exception:
                question = raw_text.strip()

            if not question:
                continue

            async with AsyncSessionLocal() as db:
                # Store user message
                user_msg = Message(
                    session_id=session_id,
                    role="user",
                    content=question,
                    citations="[]",
                )
                db.add(user_msg)

                # Update session title if first message
                result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
                curr_session = result.scalar_one_or_none()
                if curr_session and (curr_session.title == "New Chat" or not curr_session.title):
                    curr_session.title = question[:40] + ("..." if len(question) > 40 else "")
                await db.commit()

            # Stream RAG answer
            full_answer = []
            collected_citations = []

            async for event in rag_service.stream_rag_response(question):
                await websocket.send_json(event)
                if event["type"] == "token":
                    full_answer.append(event["data"])
                elif event["type"] == "citation":
                    collected_citations = event["data"]

            # Save assistant message to DB
            async with AsyncSessionLocal() as db:
                asst_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content="".join(full_answer),
                    citations=json.dumps(collected_citations),
                )
                db.add(asst_msg)
                await db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
=======
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


@router.websocket("/sessions/{session_id}/stream")
async def chat_stream_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket streaming endpoint for real-time grounded Q&A with token and citation frames."""
    # 1. Authenticate user from JWT token parameter
    user = await get_ws_current_user(websocket, token=token, db=db)
    await websocket.accept()

    try:
        await ChatService.handle_stream(websocket, session_id, user, db)
    except WebSocketDisconnect:
        pass
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
