from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    storage_path: str
    mime_type: str
    status: str
    uploaded_by: uuid.UUID
    uploaded_at: datetime
    chunk_count: int

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    chunk_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    status: str
    message: str
