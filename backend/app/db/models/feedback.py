import uuid
<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(String(20), nullable=False)  # positive | negative
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
=======
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import SmallInteger, Text, DateTime, ForeignKey, CheckConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.message import Message
    from app.db.models.user import User


class Feedback(Base):
    __tablename__ = "feedbacks"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message",
        back_populates="feedback",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="feedbacks",
    )
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
