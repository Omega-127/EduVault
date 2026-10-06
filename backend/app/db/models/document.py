import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, csv
    size_bytes = Column(Integer, default=0, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending | processing | indexed | failed
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
