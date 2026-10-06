from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


class MetadataEnricher:
    """Enriches chunk dictionaries with document-level identifiers, timestamps, and citation fields."""

    @staticmethod
    def enrich_chunks(
        chunks: List[Dict[str, Any]],
        document_id: str,
        file_name: str,
        upload_ts: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        enriched: List[Dict[str, Any]] = []
        iso_timestamp = (upload_ts or datetime.now(timezone.utc)).isoformat()

        for chunk in chunks:
            chunk_copy = chunk.copy()
            # Assign a unique chunk ID if not present
            chunk_copy["chunk_id"] = str(uuid.uuid4())
            chunk_copy["metadata"] = {
                "file_name": file_name,
                "doc_id": str(document_id),
                "page": chunk.get("page") or 1,
                "section": chunk.get("section") or "General",
                "upload_ts": iso_timestamp,
                "chunk_id": chunk_copy["chunk_id"],
            }
            enriched.append(chunk_copy)

        return enriched
