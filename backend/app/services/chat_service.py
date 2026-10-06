import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationException, EntityNotFoundException
from app.core.logging import logger
from app.db.models import ChatSession, Message, SystemLog, User
from app.rag.citation_builder import CitationBuilder
from app.rag.generator import generator
from app.rag.prompts import FALLBACK_RESPONSE
from app.rag.retriever import retriever
from app.schemas.chat import CitationItem, CreateSessionRequest


class ChatService:
    """Service handling chat session lifecycles, message histories, and WebSocket streaming."""

    @staticmethod
    async def create_session(
        db: AsyncSession,
        current_user: User,
        request: Optional[CreateSessionRequest] = None,
    ) -> ChatSession:
        title = (request.title if request and request.title else None) or "New Chat"
        session = ChatSession(
            user_id=current_user.id,
            title=title,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        current_user: User,
    ) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: uuid.UUID,
        current_user: User,
    ) -> ChatSession:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise EntityNotFoundException(f"Chat session {session_id} not found")

        # Ownership validation
        if session.user_id != current_user.id:
            raise AuthorizationException("You do not have access to this chat session")

        return session

    @staticmethod
    async def get_session_messages(
        db: AsyncSession,
        session_id: uuid.UUID,
        current_user: User,
    ) -> List[Message]:
        # Validate ownership first
        await ChatService.get_session(db, session_id, current_user)

        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def handle_stream(
        websocket: WebSocket,
        session_id: uuid.UUID,
        current_user: User,
        db: AsyncSession,
    ) -> None:
        """Manages the full lifecycle of a WebSocket streaming session."""
        session = await ChatService.get_session(db, session_id, current_user)

        while True:
            try:
                data = await websocket.receive_text()
                message_json = json.loads(data)
                question = message_json.get("question", "").strip()

                if not question:
                    continue

                # 1. Save user question
                user_msg = Message(
                    session_id=session.id,
                    role="user",
                    content=question,
                )
                db.add(user_msg)
                await db.commit()

                # 2. Retrieve context chunks with safety threshold gate
                chunks = retriever.retrieve(question)

                if not chunks:
                    # Low confidence / unanswerable: Skip LLM call entirely
                    logger.info(f"Unanswerable query detected: '{question}'")
                    await websocket.send_json({
                        "type": "token",
                        "data": FALLBACK_RESPONSE,
                    })
                    await websocket.send_json({"type": "done"})

                    # Save fallback response message
                    asst_msg = Message(
                        session_id=session.id,
                        role="assistant",
                        content=FALLBACK_RESPONSE,
                        citations=[],
                    )
                    db.add(asst_msg)

                    # Log unanswerable query in system_logs
                    log_entry = SystemLog(
                        event_type="unanswerable_query",
                        payload={
                            "session_id": str(session.id),
                            "user_id": str(current_user.id),
                            "question": question,
                        },
                    )
                    db.add(log_entry)
                    await db.commit()
                    continue

                # 3. Stream grounded LLM generation
                full_tokens: List[str] = []
                async for token in generator.stream_answer(question, chunks):
                    full_tokens.append(token)
                    await websocket.send_json({
                        "type": "token",
                        "data": token,
                    })

                complete_answer = "".join(full_tokens)

                # 4. Build and emit citations
                citations = CitationBuilder.build_citations(chunks)
                citation_payload = [c.model_dump() for c in citations]

                await websocket.send_json({
                    "type": "citation",
                    "data": citation_payload,
                })
                await websocket.send_json({"type": "done"})

                # 5. Persist assistant response with citations
                asst_msg = Message(
                    session_id=session.id,
                    role="assistant",
                    content=complete_answer,
                    citations=citation_payload,
                )
                db.add(asst_msg)
                await db.commit()

            except Exception as e:
                logger.error(f"Error during WebSocket streaming: {e}")
                break
