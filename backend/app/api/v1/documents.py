import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies import get_db, require_admin
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.user import User
from app.services.parser import parse_document
from app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    storage_path: str = ""
    mime_type: str
    status: str
    uploaded_by: str = "Admin"
    uploaded_at: datetime
    chunk_count: Optional[int] = 0

    class Config:
        from_attributes = True


async def process_document_background(
    doc_id: str,
    file_bytes: bytes,
    filename: str,
    file_type: str,
    db: AsyncSession,
):
    try:
        chunks = parse_document(file_bytes, filename, file_type)
        if not chunks:
            chunks = [{
                "chunk_index": 0,
                "content": f"Document {filename} contents uploaded.",
                "metadata": {"document_name": filename, "page": 1, "section": "General"},
                "token_count": 5,
            }]

        # Add to vector store
        vector_store.add_chunks(doc_id, chunks)

        # Update Document record
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "indexed"
            doc.chunk_count = len(chunks)
            await db.commit()
    except Exception as e:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "failed"
            await db.commit()


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=d.id,
            file_name=d.filename,
            storage_path=f"local://{d.filename}",
            mime_type=d.file_type,
            status=d.status,
            uploaded_by="Admin",
            uploaded_at=d.uploaded_at,
            chunk_count=d.chunk_count,
        )
        for d in docs
    ]


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    filename = file.filename or "uploaded_file"
    file_type = file.content_type or filename.split(".")[-1]

    doc = Document(
        filename=filename,
        file_type=file_type,
        size_bytes=len(contents),
        status="processing",
        chunk_count=0,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Ingest document
    background_tasks.add_task(
        process_document_background,
        doc.id,
        contents,
        filename,
        file_type,
        db,
    )

    return DocumentResponse(
        id=doc.id,
        file_name=doc.filename,
        storage_path=f"local://{doc.filename}",
        mime_type=doc.file_type,
        status=doc.status,
        uploaded_by=admin_user.email,
        uploaded_at=doc.uploaded_at,
        chunk_count=doc.chunk_count,
    )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete from vector store
    vector_store.delete_document(doc_id)

    # Delete from DB
    await db.delete(doc)
    await db.commit()

    return {"message": "Document deleted successfully"}
