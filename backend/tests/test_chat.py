import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models import ChatSession, Message, User


@pytest.mark.asyncio
async def test_session_creation(client: AsyncClient, student_auth_headers: dict):
    response = await client.post(
        "/api/v1/chat/sessions",
        headers=student_auth_headers,
        json={"title": "Exam Inquiries"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Exam Inquiries"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_session_list(client: AsyncClient, student_auth_headers: dict):
    # Create two sessions
    await client.post(
        "/api/v1/chat/sessions",
        headers=student_auth_headers,
        json={"title": "Session 1"},
    )
    await client.post(
        "/api/v1/chat/sessions",
        headers=student_auth_headers,
        json={"title": "Session 2"},
    )

    response = await client.get("/api/v1/chat/sessions", headers=student_auth_headers)
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) >= 2


@pytest.mark.asyncio
async def test_session_ownership_enforcement(
    client: AsyncClient,
    student_auth_headers: dict,
    db_session: AsyncSession,
):
    # Create a second user (student B)
    other_user = User(
        id=uuid.uuid4(),
        email="other@univ.edu",
        hashed_pw=get_password_hash("pass123"),
        role="student",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    other_token = create_access_token({"sub": str(other_user.id), "role": other_user.role})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Student A creates a session
    create_res = await client.post(
        "/api/v1/chat/sessions",
        headers=student_auth_headers,
        json={"title": "Student A Private Session"},
    )
    session_id = create_res.json()["id"]

    # Student B attempts to access Student A's session
    forbidden_get = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=other_headers,
    )
    assert forbidden_get.status_code == 403
    assert "do not have access" in forbidden_get.json()["detail"]

    # Student B attempts to access messages
    forbidden_messages = await client.get(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers=other_headers,
    )
    assert forbidden_messages.status_code == 403


@pytest.mark.asyncio
async def test_message_persistence(
    client: AsyncClient,
    student_auth_headers: dict,
    student_user: User,
    db_session: AsyncSession,
):
    # Create session
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=student_user.id,
        title="Persistence Test",
    )
    db_session.add(session)
    await db_session.commit()

    # Add messages
    user_msg = Message(
        session_id=session.id,
        role="user",
        content="What is the exam date?",
    )
    asst_msg = Message(
        session_id=session.id,
        role="assistant",
        content="The exam date is May 15.",
        citations=[{"document_name": "Calendar.pdf", "page": 2}],
    )
    db_session.add(user_msg)
    db_session.add(asst_msg)
    await db_session.commit()

    # Query messages API
    response = await client.get(
        f"/api/v1/chat/sessions/{session.id}/messages",
        headers=student_auth_headers,
    )
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert len(messages[1]["citations"]) == 1
    assert messages[1]["citations"][0]["document_name"] == "Calendar.pdf"
