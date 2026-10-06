from typing import Any, Dict, List
from pypdf import PdfReader
import io


class PDFParser:
    """Extracts text content and page metadata from PDF files using pypdf."""

    @staticmethod
    def parse(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """Parses PDF bytes and returns page-level text items with page numbers."""
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_content: List[Dict[str, Any]] = []

        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_content.append({
                    "text": text.strip(),
                    "page": index + 1,  # 1-indexed page number
                    "section": None,
                })

        return pages_content
