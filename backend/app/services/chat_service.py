import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationException, EntityNotFoundException, ValidationException
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
    async def answer_question(
        db: AsyncSession,
        session_id: uuid.UUID,
        current_user: User,
        question: str,
    ) -> Tuple[Message, Message]:
        """Runs retrieval + generation and persists both user and assistant messages."""
        session = await ChatService.get_session(db, session_id, current_user)
        question = (question or "").strip()
        if not question:
            raise ValidationException("Question cannot be empty")

        user_msg = Message(
            session_id=session.id,
            role="user",
            content=question,
        )
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)

        try:
            chunks = retriever.retrieve(question)
        except Exception as e:
            logger.error(f"Retrieval failed for question '{question}': {e}")
            chunks = None

        if not chunks:
            logger.info(f"Unanswerable query detected: '{question}'")
            asst_msg = Message(
                session_id=session.id,
                role="assistant",
                content=FALLBACK_RESPONSE,
                citations=[],
            )
            db.add(asst_msg)
            db.add(
                SystemLog(
                    event_type="unanswerable_query",
                    payload={
                        "session_id": str(session.id),
                        "user_id": str(current_user.id),
                        "question": question,
                    },
                )
            )
            await db.commit()
            await db.refresh(asst_msg)
            return user_msg, asst_msg

        try:
            full_tokens: List[str] = []
            async for token in generator.stream_answer(question, chunks):
                full_tokens.append(token)
            complete_answer = "".join(full_tokens)
            citations = CitationBuilder.build_citations(chunks)
            citation_payload = [c.model_dump() for c in citations]
        except Exception as e:
            logger.error(f"Generation failed for question '{question}': {e}")
            complete_answer = FALLBACK_RESPONSE
            citation_payload = []

        asst_msg = Message(
            session_id=session.id,
            role="assistant",
            content=complete_answer,
            citations=citation_payload,
        )
        db.add(asst_msg)
        await db.commit()
        await db.refresh(asst_msg)
        return user_msg, asst_msg

    @staticmethod
    async def handle_stream(
        websocket: WebSocket,
        session_id: uuid.UUID,
        current_user: User,
        db: AsyncSession,
    ) -> None:
        """Manages the full lifecycle of a WebSocket streaming session."""
        try:
            session = await ChatService.get_session(db, session_id, current_user)
        except Exception as e:
            logger.error(f"WebSocket session validation failed: {e}")
            await websocket.send_json({
                "type": "error",
                "data": str(getattr(e, "message", e)),
            })
            return

        while True:
            try:
                data = await websocket.receive_text()
                message_json = json.loads(data)
                question = message_json.get("question", "").strip()

                if not question:
                    continue

                user_msg, asst_msg = await ChatService.answer_question(
                    db, session.id, current_user, question
                )

                # Stream the already-generated answer for WS clients
                await websocket.send_json({
                    "type": "token",
                    "data": asst_msg.content,
                })
                if asst_msg.citations:
                    await websocket.send_json({
                        "type": "citation",
                        "data": asst_msg.citations,
                    })
                await websocket.send_json({"type": "done"})
                _ = user_msg  # persisted in answer_question

            except Exception as e:
                logger.error(f"Error during WebSocket streaming: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "data": f"Error generating answer: {str(e)}",
                    })
                    await websocket.send_json({"type": "done"})
                except Exception:
                    pass
                break
