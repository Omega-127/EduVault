import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    citations = Column(Text, default="[]", nullable=False)  # JSON-encoded array of citations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
