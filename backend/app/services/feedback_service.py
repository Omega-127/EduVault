import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.db.models import Feedback, Message, User
from app.schemas.feedback import FeedbackCreateRequest


class FeedbackService:
    """Service handling submission and querying of user response ratings."""

    @staticmethod
    async def create_feedback(
        db: AsyncSession,
        request: FeedbackCreateRequest,
        current_user: User,
    ) -> Feedback:
        if request.rating < 1 or request.rating > 5:
            raise ValidationException("Rating must be an integer between 1 and 5")

        # Verify message exists
        msg_result = await db.execute(select(Message).where(Message.id == request.message_id))
        msg = msg_result.scalar_one_or_none()
        if not msg:
            raise EntityNotFoundException(f"Message {request.message_id} not found")

        feedback = Feedback(
            message_id=request.message_id,
            user_id=current_user.id,
            rating=request.rating,
            comment=request.comment,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback
