<<<<<<< HEAD
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.db.models.feedback import Feedback
from app.db.models.user import User
=======
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

router = APIRouter(prefix="/feedback", tags=["Feedback"])


<<<<<<< HEAD
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
=======
@router.post(
    "/",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user rating and feedback for an assistant message",
)
async def submit_feedback(
    request: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submits a rating between 1 and 5 and optional comment for a generated assistant response."""
    feedback = await FeedbackService.create_feedback(db, request, current_user)
    return FeedbackResponse.model_validate(feedback)
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
