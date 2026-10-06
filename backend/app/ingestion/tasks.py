import asyncio
import traceback
import uuid
from typing import Any, Dict

from celery import shared_task
from sqlalchemy import select

from app.core.logging import logger
from app.db.models import Document, DocumentChunk, SystemLog
from app.db.session import AsyncSessionLocal
from app.ingestion.chunker import DocumentChunker
from app.ingestion.embedder import embedder
from app.ingestion.metadata_enricher import MetadataEnricher
from app.ingestion.parsers import get_parser
from app.storage.object_store import object_store
from app.storage.vector_store import vector_store
from app.worker.celery_app import celery_app


async def _async_ingest_document(document_id: str) -> Dict[str, Any]:
    """Asynchronous core ingestion logic executed by the Celery task."""
    doc_uuid = uuid.UUID(document_id)

    async with AsyncSessionLocal() as db:
        # Step 1: Find document record
        result = await db.execute(select(Document).where(Document.id == doc_uuid))
        document = result.scalar_one_or_none()
        if not document:
            logger.error(f"Document {document_id} not found for ingestion")
            return {"status": "error", "message": "Document not found"}

        # Step 1a: Set status to processing
        document.status = "processing"
        await db.commit()
        await db.refresh(document)

    try:
        # Step 2: Download document from object store
        logger.info(f"Downloading raw document from {document.storage_path}")
        file_bytes = object_store.get(document.storage_path)

        # Step 3 & 4: Select parser and extract text
        parser = get_parser(document.mime_type, document.file_name)
        logger.info(f"Parsing document using {parser.__name__}")
        parsed_items = parser.parse(file_bytes, document.file_name)

        if not parsed_items:
            logger.warning(f"No text extracted from document {document.file_name}")

        # Step 5: Split text into chunks
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        raw_chunks = chunker.split_parsed_items(parsed_items)

        # Step 6: Enrich metadata
        enriched_chunks = MetadataEnricher.enrich_chunks(
            chunks=raw_chunks,
            document_id=str(document.id),
            file_name=document.file_name,
            upload_ts=document.uploaded_at,
        )

        logger.info(f"Generated {len(enriched_chunks)} chunks for document {document.file_name}")

        # Step 7 & 8: Batch embed and store in Vector Database
        if enriched_chunks:
            chunk_texts = [c["text"] for c in enriched_chunks]
            chunk_ids = [c["chunk_id"] for c in enriched_chunks]
            metadatas = [c["metadata"] for c in enriched_chunks]

            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
            embeddings = embedder.embed_documents(chunk_texts)

            logger.info("Upserting vectors into vector store...")
            vector_store.upsert(
                ids=chunk_ids,
                vectors=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )

        # Step 9, 10, 11: Update database with chunks and status
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == doc_uuid))
            doc_to_update = result.scalar_one()

            # Insert chunk records
            for c in enriched_chunks:
                chunk_record = DocumentChunk(
                    id=uuid.UUID(c["chunk_id"]),
                    document_id=doc_to_update.id,
                    text=c["text"],
                    page=c.get("page"),
                    section=c.get("section"),
                    vector_id=c["chunk_id"],
                )
                db.add(chunk_record)

            doc_to_update.status = "indexed"
            doc_to_update.chunk_count = len(enriched_chunks)
            await db.commit()

        logger.info(f"Document {document_id} successfully indexed with {len(enriched_chunks)} chunks")
        return {"status": "indexed", "chunk_count": len(enriched_chunks)}

    except Exception as e:
        error_msg = str(e)
        stack = traceback.format_exc()
        logger.error(f"Ingestion failed for document {document_id}: {error_msg}\n{stack}")

        # Mark document as failed and record system log
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == doc_uuid))
            failed_doc = result.scalar_one_or_none()
            if failed_doc:
                failed_doc.status = "failed"

            # Create system log
            log_entry = SystemLog(
                event_type="ingestion_failed",
                payload={
                    "document_id": str(document_id),
                    "error": error_msg,
                },
            )
            db.add(log_entry)
            await db.commit()

        raise e


@celery_app.task(
    name="app.ingestion.tasks.ingest_document",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def ingest_document(self, document_id: str):
    """Celery task entrypoint for async document ingestion."""
    logger.info(f"Starting Celery ingestion task for document_id={document_id}")
    try:
        return asyncio.run(_async_ingest_document(document_id))
    except Exception as exc:
        logger.warning(f"Task failed, retrying if possible: {exc}")
        # Allow retry on transient failures
        try:
            raise self.retry(exc=exc)
        except Exception:
            raise exc
