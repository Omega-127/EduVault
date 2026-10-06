from datetime import datetime
from typing import Any, List, Optional
import uuid
from pydantic import BaseModel
from app.schemas.auth import UserResponse


class SystemLogResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    payload: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemLogListResponse(BaseModel):
    total: int
    logs: List[SystemLogResponse]


class AdminUserListResponse(BaseModel):
    total: int
    users: List[UserResponse]


class AdminStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_indexed_chunks: int
    total_chat_sessions: int
    total_messages: int
    total_feedbacks: int
    unanswerable_queries_count: int
