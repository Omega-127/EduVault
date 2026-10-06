from typing import Any, Dict, List
from app.storage.vector_store import VectorQueryResult

SYSTEM_PROMPT = """You are EduVault, a university knowledge assistant.
Answer ONLY using the provided context passages.

If the context does not contain the answer, respond exactly:
"Information not found in the institutional knowledge base."

Do not speculate.
Do not infer.
Do not answer from general knowledge.
Always cite document name and page number when available."""

FALLBACK_RESPONSE = "Information not found in the institutional knowledge base."


def build_context_string(chunks: List[VectorQueryResult]) -> str:
    """Formats retrieved chunks into clear, cited context blocks."""
    passages = []
    for idx, c in enumerate(chunks, 1):
        meta = c.metadata or {}
        doc_name = meta.get("file_name", "Unknown Document")
        page = meta.get("page", 1)
        section = meta.get("section", "General")
        passages.append(
            f"--- [Passage {idx} | Source: {doc_name} | Page: {page} | Section: {section}] ---\n"
            f"{c.text.strip()}\n"
        )
    return "\n".join(passages)


def build_rag_prompt(question: str, chunks: List[VectorQueryResult]) -> str:
    """Combines context and student question into the complete RAG prompt."""
    context_str = build_context_string(chunks)
    return (
        f"CONTEXT:\n"
        f"{context_str}\n\n"
        f"USER QUESTION:\n"
        f"{question.strip()}\n\n"
        f"ANSWER:"
    )
