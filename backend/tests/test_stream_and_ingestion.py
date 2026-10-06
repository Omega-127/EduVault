import io
import uuid
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import select
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.ingestion.parsers.docx_parser import DOCXParser
from app.ingestion.parsers.txt_parser import TXTParser
from app.main import app
from app.rag.prompts import FALLBACK_RESPONSE
from app.storage.vector_store import VectorQueryResult
from tests.conftest import TestingSessionLocal


def test_txt_parser():
    sample_text = b"Line 1 text.\n\nLine 2 text with info."
    results = TXTParser.parse(sample_text, "info.txt")
    assert len(results) == 2
    assert results[0]["text"] == "Line 1 text."
    assert results[1]["text"] == "Line 2 text with info."


def test_docx_parser():
    with patch("docx2txt.process", return_value="Section Title\n\nParagraph details under section."):
        results = DOCXParser.parse(b"dummy docx bytes", "memo.docx")
        assert len(results) == 2
        assert results[0]["section"] == "Section Title"
        assert "Paragraph details" in results[1]["text"]


@pytest.fixture(autouse=True)
def override_test_db():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


def test_websocket_stream_unanswerable_query(student_user: User):
    token = create_access_token({"sub": str(student_user.id), "role": student_user.role})

    with TestClient(app) as client:
        create_res = client.post(
            "/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "WS Test"},
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        with patch("app.rag.retriever.retriever.retrieve", return_value=None):
            with client.websocket_connect(f"/api/v1/chat/sessions/{session_id}/stream?token={token}") as ws:
                ws.send_json({"question": "What is quantum gravity?"})

                frame1 = ws.receive_json()
                assert frame1["type"] == "token"
                assert frame1["data"] == FALLBACK_RESPONSE

                frame2 = ws.receive_json()
                assert frame2["type"] == "done"


def test_websocket_stream_grounded_answer(student_user: User):
    token = create_access_token({"sub": str(student_user.id), "role": student_user.role})

    with TestClient(app) as client:
        create_res = client.post(
            "/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "WS Grounded Test"},
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        mock_chunk = VectorQueryResult(
            id="c-test-1",
            text="The library opens at 8:00 AM daily.",
            distance=0.12,
            metadata={
                "file_name": "Handbook.pdf",
                "page": 10,
                "section": "Library Facilities",
                "chunk_id": "c-test-1",
            },
        )

        with patch("app.rag.retriever.retriever.retrieve", return_value=[mock_chunk]):
            with client.websocket_connect(f"/api/v1/chat/sessions/{session_id}/stream?token={token}") as ws:
                ws.send_json({"question": "When does the library open?"})

                tokens = []
                citations = []
                while True:
                    frame = ws.receive_json()
                    if frame["type"] == "token":
                        tokens.append(frame["data"])
                    elif frame["type"] == "citation":
                        citations.extend(frame["data"])
                    elif frame["type"] == "done":
                        break

                assert len(tokens) > 0
                assert len(citations) == 1
                assert citations[0]["document_name"] == "Handbook.pdf"
                assert citations[0]["page"] == 10
                assert citations[0]["section"] == "Library Facilities"


def test_websocket_rejects_missing_token():
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/chat/sessions/{uuid.uuid4()}/stream"):
            pass
