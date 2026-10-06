import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for async ingestion (Admin only)",
)
async def upload_document(
    file: UploadFile = File(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Uploads a PDF, DOCX, TXT, or CSV file to object storage and queues background ingestion."""
    doc = await DocumentService.upload_document(db, file, admin_user)
    return DocumentUploadResponse(
        id=doc.id,
        file_name=doc.file_name,
        status=doc.status,
        message="Document uploaded and ingestion queued successfully.",
    )


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns a list of all documents with pagination."""
    docs, total = await DocumentService.list_documents(db, skip=skip, limit=limit)
    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Retrieve details of a single document",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns full metadata for the specified document."""
    doc = await DocumentService.get_document(db, document_id)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Check ingestion job status of a document",
)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the current ingestion status (pending, processing, indexed, failed)."""
    doc = await DocumentService.get_document(db, document_id)
    return DocumentStatusResponse.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document, raw file, and semantic vectors (Admin only)",
)
async def delete_document(
    document_id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deletes document records, object storage file, and indexed chunks from vector store."""
    await DocumentService.delete_document(db, document_id)
    return None
