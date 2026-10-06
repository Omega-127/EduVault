import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from app.db.base import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)  # section, page, etc.
    token_count = Column(Integer, default=0, nullable=False)
