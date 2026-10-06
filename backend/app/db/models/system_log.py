import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.db.base import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)  # ingestion_started, unanswerable_query, etc.
    payload = Column(Text, default="{}", nullable=False)  # JSON-encoded metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
