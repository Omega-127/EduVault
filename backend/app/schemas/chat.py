from datetime import datetime
from typing import Any, List, Literal, Optional
import uuid
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CitationItem(BaseModel):
    document_name: str
    doc_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    snippet: Optional[str] = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    # Accept any JSON shape so malformed/legacy citation payloads don't 500 the chat
    citations: Optional[List[Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatAskResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class StreamTokenFrame(BaseModel):
    type: Literal["token"] = "token"
    data: str


class StreamCitationFrame(BaseModel):
    type: Literal["citation"] = "citation"
    data: List[CitationItem]


class StreamDoneFrame(BaseModel):
    type: Literal["done"] = "done"
