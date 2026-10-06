from typing import Any, Dict, List, Set, Tuple
from app.schemas.chat import CitationItem
from app.storage.vector_store import VectorQueryResult


class CitationBuilder:
    """Builds and deduplicates structured citation items from retrieved vector chunks."""

    @staticmethod
    def build_citations(chunks: List[VectorQueryResult]) -> List[CitationItem]:
        citations: List[CitationItem] = []
        seen: Set[Tuple[str, Any, Any]] = set()

        for chunk in chunks:
            meta = chunk.metadata or {}
            doc_name = meta.get("file_name") or "Unknown Document"
            page_val = meta.get("page")
            try:
                page = int(page_val) if page_val is not None and str(page_val).strip() != "" else None
            except (ValueError, TypeError):
                page = None

            section = meta.get("section") or None
            chunk_id = meta.get("chunk_id") or chunk.id

            key = (doc_name, page, section)
            if key not in seen:
                seen.add(key)
                citations.append(
                    CitationItem(
                        document_name=doc_name,
                        page=page,
                        section=section,
                        chunk_id=chunk_id,
                    )
                )

        return citations
