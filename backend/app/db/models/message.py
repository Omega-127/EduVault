import uuid
<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.db.base import Base

=======
from datetime import datetime, timezone
from typing import Any, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_session import ChatSession
    from app.db.models.feedback import Feedback

>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

class Message(Base):
    __tablename__ = "messages"

<<<<<<< HEAD
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    citations = Column(Text, default="[]", nullable=False)  # JSON-encoded array of citations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
=======
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,  # "user" or "assistant"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    citations: Mapped[Optional[List[Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )
    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
