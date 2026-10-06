from typing import Any, Dict, List


class TXTParser:
    """Extracts text content from plain text files."""

    @staticmethod
    def parse(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1", errors="replace")

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content.strip()] if content.strip() else []

        return [
            {
                "text": p,
                "page": 1,
                "section": None,
            }
            for p in paragraphs
        ]
