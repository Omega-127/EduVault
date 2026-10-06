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

router = APIRouter(prefix="/chat", tags=["Chat"])


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
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
