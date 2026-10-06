import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.core.logging import logger
from app.db.models import Document, User
from app.ingestion.tasks import ingest_document
from app.storage.object_store import object_store
from app.storage.vector_store import vector_store

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "application/csv",
}


class DocumentService:
    """Service handling document uploads, queries, and deletion."""

    @staticmethod
    def _validate_file(file: UploadFile) -> None:
        filename = file.filename or ""
        lower_name = filename.lower()
        has_allowed_ext = any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        content_type = (file.content_type or "").lower()

        if not has_allowed_ext and content_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                f"Unsupported file format for '{filename}'. Supported types: PDF, DOCX, TXT, CSV."
            )

    @staticmethod
    async def upload_document(
        db: AsyncSession,
        file: UploadFile,
        current_user: User,
    ) -> Document:
        DocumentService._validate_file(file)

        doc_id = uuid.uuid4()
        clean_filename = file.filename or "uploaded_document"
        storage_path = f"raw/{doc_id}/{clean_filename}"

        # Read file bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise ValidationException("The uploaded file is empty.")

        # Ensure MinIO bucket exists and upload file
        object_store.ensure_bucket_exists()
        object_store.put(
            key=storage_path,
            data=file_bytes,
            content_type=file.content_type or "application/octet-stream",
        )

        # Create database record
        doc = Document(
            id=doc_id,
            file_name=clean_filename,
            storage_path=storage_path,
            mime_type=file.content_type or "application/octet-stream",
            status="pending",
            uploaded_by=current_user.id,
            chunk_count=0,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        # Dispatch Celery ingestion task asynchronously, with asyncio fallback
        try:
            ingest_document.delay(str(doc.id))
            logger.info(f"Dispatched Celery ingestion task for document {doc.id}")
        except Exception as e:
            logger.warning(f"Could not dispatch Celery task via broker ({e}). Running in background task fallback.")
            import asyncio
            from app.ingestion.tasks import _async_ingest_document
            asyncio.create_task(_async_ingest_document(str(doc.id)))

        return doc

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Document], int]:
        total_result = await db.execute(select(func.count(Document.id)))
        total = total_result.scalar_one()

        result = await db.execute(
            select(Document)
            .order_by(Document.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())
        return documents, total

    @staticmethod
    async def get_document(db: AsyncSession, doc_id: uuid.UUID) -> Document:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise EntityNotFoundException(f"Document with ID {doc_id} not found")
        return doc

    @staticmethod
    async def get_document_file(db: AsyncSession, doc_id: uuid.UUID) -> Tuple[bytes, str, str]:
        doc = await DocumentService.get_document(db, doc_id)
        file_bytes = object_store.get(doc.storage_path)
        return file_bytes, doc.mime_type, doc.file_name

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: uuid.UUID) -> None:
        doc = await DocumentService.get_document(db, doc_id)

        # Delete raw file from MinIO / S3
        try:
            object_store.delete(doc.storage_path)
        except Exception as e:
            logger.warning(f"Could not delete storage file {doc.storage_path}: {e}")

        # Delete indexed vectors from Vector Store
        try:
            vector_store.delete_by_document_id(str(doc.id))
        except Exception as e:
            logger.warning(f"Could not delete vectors for document {doc.id}: {e}")

        # Delete database record (chunks cascade delete automatically)
        await db.delete(doc)
        await db.commit()
        logger.info(f"Document {doc_id} and related data deleted successfully.")
