import io
import re
from typing import List, Dict, Any


def chunk_text(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks while preserving metadata."""
    chunks = []
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return chunks

    start = 0
    index = 0
    while start < len(text):
        end = start + chunk_size
        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append({
                "chunk_index": index,
                "content": chunk_str,
                "metadata": metadata.copy(),
                "token_count": len(chunk_str.split()),
            })
            index += 1
        start += chunk_size - chunk_overlap
    return chunks


def parse_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    all_chunks = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        meta = {
            "document_name": filename,
            "page": page_num,
            "section": f"Page {page_num}",
        }
        page_chunks = chunk_text(text, meta)
        all_chunks.extend(page_chunks)
        
    return all_chunks


def parse_docx(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    all_chunks = []
    current_section = "General"
    accumulated_text = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style.name.startswith("Heading"):
            if accumulated_text:
                meta = {
                    "document_name": filename,
                    "page": 1,
                    "section": current_section,
                }
                all_chunks.extend(chunk_text(" ".join(accumulated_text), meta))
                accumulated_text = []
            current_section = text
        else:
            accumulated_text.append(text)

    if accumulated_text:
        meta = {
            "document_name": filename,
            "page": 1,
            "section": current_section,
        }
        all_chunks.extend(chunk_text(" ".join(accumulated_text), meta))

    return all_chunks


def parse_txt(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    text = file_bytes.decode("utf-8", errors="ignore")
    meta = {
        "document_name": filename,
        "page": 1,
        "section": "General",
    }
    return chunk_text(text, meta)


def parse_csv(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    import pandas as pd
    df = pd.read_csv(io.BytesIO(file_bytes))
    all_chunks = []
    
    # Chunk by rows in batches of 10
    batch_size = 10
    for i in range(0, len(df), batch_size):
        sub_df = df.iloc[i : i + batch_size]
        text_repr = sub_df.to_string(index=False)
        meta = {
            "document_name": filename,
            "page": 1,
            "section": f"Rows {i+1} to {min(i + batch_size, len(df))}",
        }
        all_chunks.extend(chunk_text(text_repr, meta))
        
    return all_chunks


def parse_document(file_bytes: bytes, filename: str, file_type: str) -> List[Dict[str, Any]]:
    ext = file_type.lower().replace(".", "")
    if ext == "pdf":
        return parse_pdf(file_bytes, filename)
    elif ext in ("docx", "doc"):
        return parse_docx(file_bytes, filename)
    elif ext == "csv":
        return parse_csv(file_bytes, filename)
    elif ext in ("txt", "md"):
        return parse_txt(file_bytes, filename)
    else:
        # Default text fallback
        return parse_txt(file_bytes, filename)
