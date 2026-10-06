from unittest.mock import MagicMock, patch
import pytest

from app.ingestion.chunker import DocumentChunker
from app.ingestion.parsers.csv_parser import CSVParser
from app.rag.citation_builder import CitationBuilder
from app.rag.prompts import FALLBACK_RESPONSE
from app.rag.retriever import RAGRetriever
from app.storage.vector_store import VectorQueryResult


def test_chunker_splitting():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    parsed_items = [
        {"text": "Paragraph 1 is here.\n\nParagraph 2 is here with additional text.", "page": 1, "section": "Intro"}
    ]
    chunks = chunker.split_parsed_items(parsed_items)
    assert len(chunks) >= 1
    assert chunks[0]["page"] == 1
    assert chunks[0]["section"] == "Intro"


def test_csv_parser_key_value_rows():
    csv_bytes = b"Course,Code,Credits\nDatabase Systems,CS301,4\nAlgorithms,CS201,4"
    results = CSVParser.parse(csv_bytes, "courses.csv")
    assert len(results) == 2
    assert "Course: Database Systems" in results[0]["text"]
    assert "Credits: 4" in results[0]["text"]
    assert results[0]["section"] == "Row 1"


def test_citation_builder():
    sample_chunks = [
        VectorQueryResult(
            id="chunk-1",
            text="Minimum attendance required is 75%.",
            distance=0.15,
            metadata={
                "file_name": "Attendance Policy 2026.pdf",
                "page": 4,
                "section": "2.1 Minimum Attendance",
                "chunk_id": "chunk-1",
            },
        ),
        VectorQueryResult(
            id="chunk-2",
            text="Medical leaves require prior approval.",
            distance=0.22,
            metadata={
                "file_name": "Attendance Policy 2026.pdf",
                "page": 4,
                "section": "2.1 Minimum Attendance",
                "chunk_id": "chunk-2",
            },
        ),
    ]

    citations = CitationBuilder.build_citations(sample_chunks)
    # Deduplication by (doc, page, section) should produce 1 citation item
    assert len(citations) == 1
    assert citations[0].document_name == "Attendance Policy 2026.pdf"
    assert citations[0].page == 4
    assert citations[0].section == "2.1 Minimum Attendance"


def test_retrieval_safety_gate_success():
    retriever = RAGRetriever(top_k=2, threshold=0.35)

    mock_results = [
        VectorQueryResult(
            id="c1",
            text="75 percent attendance required",
            distance=0.18,  # Below threshold
            metadata={"file_name": "policy.pdf", "page": 1},
        )
    ]

    with patch("app.ingestion.embedder.embedder.embed_query", return_value=[0.1] * 384), \
         patch("app.storage.vector_store.vector_store.query", return_value=mock_results):

        result = retriever.retrieve("What is the attendance?")
        assert result is not None
        assert len(result) == 1
        assert result[0].distance == 0.18


def test_retrieval_safety_gate_rejects_low_confidence():
    retriever = RAGRetriever(top_k=2, threshold=0.35)

    mock_results = [
        VectorQueryResult(
            id="c1",
            text="Unrelated text about sports",
            distance=0.62,  # Exceeds threshold 0.35
            metadata={"file_name": "sports.pdf", "page": 5},
        )
    ]

    with patch("app.ingestion.embedder.embedder.embed_query", return_value=[0.1] * 384), \
         patch("app.storage.vector_store.vector_store.query", return_value=mock_results):

        result = retriever.retrieve("What is the tuition fee?")
        # Must return None so LLM is not called
        assert result is None
