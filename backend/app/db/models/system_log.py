import uuid
<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
=======
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import String, DateTime, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
from app.db.base import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

<<<<<<< HEAD
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)  # ingestion_started, unanswerable_query, etc.
    payload = Column(Text, default="{}", nullable=False)  # JSON-encoded metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
=======
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    payload: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
