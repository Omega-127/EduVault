from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


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
