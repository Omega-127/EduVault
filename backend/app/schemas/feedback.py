from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    message_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
