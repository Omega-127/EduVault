from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.db.models.feedback import Feedback
from app.db.models.user import User

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackCreate(BaseModel):
    message_id: str
    rating: str  # positive | negative
    comment: Optional[str] = None


@router.post("/")
async def create_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback = Feedback(
        message_id=data.message_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(feedback)
    await db.commit()
    return {"status": "success", "message": "Feedback submitted"}
