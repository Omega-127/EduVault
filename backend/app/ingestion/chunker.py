from typing import Any, Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Splits parsed text items into overlapping chunks while preserving origin metadata."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
        )

    def split_parsed_items(self, parsed_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Takes raw parsed page/row/paragraph items and splits their text into chunks."""
        chunks: List[Dict[str, Any]] = []

        for item in parsed_items:
            raw_text = item.get("text", "")
            if not raw_text.strip():
                continue

            text_splits = self.splitter.split_text(raw_text)
            for split_text in text_splits:
                if split_text.strip():
                    chunks.append({
                        "text": split_text.strip(),
                        "page": item.get("page"),
                        "section": item.get("section"),
                    })

        return chunks
