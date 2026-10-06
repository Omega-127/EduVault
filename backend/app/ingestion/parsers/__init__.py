from typing import Any, Dict, List
from app.core.exceptions import IngestionException
from app.ingestion.parsers.pdf_parser import PDFParser
from app.ingestion.parsers.docx_parser import DOCXParser
from app.ingestion.parsers.txt_parser import TXTParser
from app.ingestion.parsers.csv_parser import CSVParser


def get_parser(mime_type: str, file_name: str):
    """Returns the appropriate parser according to the document's MIME type or extension."""
    mime = mime_type.lower()
    name = file_name.lower()

    if "pdf" in mime or name.endswith(".pdf"):
        return PDFParser
    elif "word" in mime or "docx" in mime or name.endswith(".docx"):
        return DOCXParser
    elif "csv" in mime or name.endswith(".csv"):
        return CSVParser
    elif "text/plain" in mime or name.endswith(".txt"):
        return TXTParser
    else:
        raise IngestionException(f"Unsupported file format: {mime_type} ({file_name})")
