import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, Message, User


@pytest_asyncio.fixture
async def sample_message(db_session: AsyncSession, student_user: User) -> Message:
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=student_user.id,
        title="Feedback Session",
    )
    db_session.add(session)
    await db_session.commit()

    msg = Message(
        id=uuid.uuid4(),
        session_id=session.id,
        role="assistant",
        content="This is an assistant response.",
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


@pytest.mark.asyncio
async def test_valid_feedback_submission(
    client: AsyncClient,
    student_auth_headers: dict,
    sample_message: Message,
):
    response = await client.post(
        "/api/v1/feedback/",
        headers=student_auth_headers,
        json={
            "message_id": str(sample_message.id),
            "rating": 5,
            "comment": "Very accurate and helpful citation!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "Very accurate and helpful citation!"
    assert data["message_id"] == str(sample_message.id)


@pytest.mark.asyncio
async def test_invalid_feedback_rating_too_high(
    client: AsyncClient,
    student_auth_headers: dict,
    sample_message: Message,
):
    response = await client.post(
        "/api/v1/feedback/",
        headers=student_auth_headers,
        json={
            "message_id": str(sample_message.id),
            "rating": 6,  # Invalid: > 5
            "comment": "Too high rating",
        },
    )
    # Pydantic validation fails with 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_feedback_rating_too_low(
    client: AsyncClient,
    student_auth_headers: dict,
    sample_message: Message,
):
    response = await client.post(
        "/api/v1/feedback/",
        headers=student_auth_headers,
        json={
            "message_id": str(sample_message.id),
            "rating": 0,  # Invalid: < 1
            "comment": "Zero rating",
        },
    )
    assert response.status_code == 422
