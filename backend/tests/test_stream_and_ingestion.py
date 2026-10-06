import io
import json
import uuid
from unittest.mock import MagicMock, patch
import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.db.models import ChatSession, Document, Message, User
from app.ingestion.parsers.docx_parser import DOCXParser
from app.ingestion.parsers.txt_parser import TXTParser
from app.ingestion.tasks import _async_ingest_document
from app.rag.prompts import FALLBACK_RESPONSE
from app.services.chat_service import ChatService
from app.storage.vector_store import VectorQueryResult


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


class MockWebSocket:
    """Mock WebSocket for async deterministic streaming tests."""
    def __init__(self, incoming_json_messages):
        self.incoming = [json.dumps(m) for m in incoming_json_messages]
        self.sent = []

    async def receive_text(self) -> str:
        if not self.incoming:
            raise WebSocketDisconnect()
        return self.incoming.pop(0)

    async def send_json(self, data) -> None:
        self.sent.append(data)


@pytest.mark.asyncio
async def test_chat_stream_unanswerable_query(student_user: User, db_session):
    # 1. Create chat session
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=student_user.id,
        title="Unanswerable Test",
    )
    db_session.add(session)
    await db_session.commit()

    mock_ws = MockWebSocket([{"question": "What is the secret formula?"}])

    with patch("app.rag.retriever.retriever.retrieve", return_value=None):
        await ChatService.handle_stream(mock_ws, session.id, student_user, db_session)

    # Verify fallback response frames
    assert len(mock_ws.sent) == 2
    assert mock_ws.sent[0]["type"] == "token"
    assert mock_ws.sent[0]["data"] == FALLBACK_RESPONSE
    assert mock_ws.sent[1]["type"] == "done"


@pytest.mark.asyncio
async def test_chat_stream_grounded_answer(student_user: User, db_session):
    # 1. Create chat session
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=student_user.id,
        title="Grounded Stream Test",
    )
    db_session.add(session)
    await db_session.commit()

    mock_chunk = VectorQueryResult(
        id="chunk-test-1",
        text="The campus health center operates Monday through Friday from 9 AM to 5 PM.",
        distance=0.15,
        metadata={
            "file_name": "HealthCenterGuide.pdf",
            "page": 3,
            "section": "Operating Hours",
            "chunk_id": "chunk-test-1",
        },
    )

    mock_ws = MockWebSocket([{"question": "What are the health center hours?"}])

    with patch("app.rag.retriever.retriever.retrieve", return_value=[mock_chunk]):
        await ChatService.handle_stream(mock_ws, session.id, student_user, db_session)

    # Verify streamed frames
    tokens = [f["data"] for f in mock_ws.sent if f["type"] == "token"]
    citations = [f["data"] for f in mock_ws.sent if f["type"] == "citation"]
    done_frames = [f for f in mock_ws.sent if f["type"] == "done"]

    assert len(tokens) > 0
    assert len(citations) == 1
    assert len(done_frames) == 1

    first_citation = citations[0][0]
    assert first_citation["document_name"] == "HealthCenterGuide.pdf"
    assert first_citation["page"] == 3
    assert first_citation["section"] == "Operating Hours"


@pytest.mark.asyncio
async def test_end_to_end_async_ingest_document(student_user: User, db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        file_name="regulations.txt",
        storage_path=f"raw/{doc_id}/regulations.txt",
        mime_type="text/plain",
        status="pending",
        uploaded_by=student_user.id,
        chunk_count=0,
    )
    db_session.add(doc)
    await db_session.commit()

    sample_doc_bytes = b"Students must maintain 75% attendance to sit for semester examinations.\n\nAbsence requires approval."

    with patch("app.storage.object_store.object_store.get", return_value=sample_doc_bytes), \
         patch("app.ingestion.embedder.embedder.embed_documents", return_value=[[0.05] * 384, [0.06] * 384]), \
         patch("app.storage.vector_store.vector_store.upsert") as mock_upsert:

        result = await _async_ingest_document(str(doc_id))
        assert result["status"] == "indexed"
        assert result["chunk_count"] == 2
        mock_upsert.assert_called_once()
