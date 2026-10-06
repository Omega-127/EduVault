import io
import tempfile
import os
from typing import Any, Dict, List
import docx2txt


class DOCXParser:
    """Extracts text content and paragraph/section structure from DOCX files."""

    @staticmethod
    def parse(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        # docx2txt requires a file path or file-like object
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            raw_text = docx2txt.process(temp_path)
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

            results: List[Dict[str, Any]] = []
            current_section = None

            for p in paragraphs:
                # Basic heuristic: short lines without terminal punctuation can serve as section headers
                if len(p) < 80 and not p.endswith(".") and "\n" not in p:
                    current_section = p
                results.append({
                    "text": p,
                    "page": 1,
                    "section": current_section,
                })

            if not results and raw_text.strip():
                results.append({
                    "text": raw_text.strip(),
                    "page": 1,
                    "section": None,
                })

            return results
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
