from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.core.exceptions import StorageException
from app.core.logging import logger


class VectorQueryResult(BaseModel):
    id: str
    text: str
    distance: float
    metadata: Dict[str, Any]


class BaseVectorStore(ABC):
    """Abstract base class for vector database implementations."""

    @abstractmethod
    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Upserts embedded vectors and associated documents & metadata."""
        pass

    @abstractmethod
    def query(
        self,
        query_vector: List[float],
        top_k: int = 4,
    ) -> List[VectorQueryResult]:
        """Queries the vector database for nearest neighbors."""
        pass

    @abstractmethod
    def delete_by_document_id(self, document_id: str) -> None:
        """Deletes all chunks associated with the specified document ID."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation of the VectorStore abstraction."""

    COLLECTION_NAME = "eduvault_chunks"

    def __init__(self):
        self.client = self._init_client()
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _init_client(self):
        """Initializes ChromaDB HTTP client with graceful fallback to PersistentClient."""
        try:
            # Try connecting to external ChromaDB service
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            # Test heartbeat
            client.heartbeat()
            logger.info(f"Connected to remote ChromaDB server at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
            return client
        except Exception as e:
            logger.info(f"Remote ChromaDB not available ({e}). Using local PersistentClient at ./chroma_data")
            return chromadb.PersistentClient(path="./chroma_data")

    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return

        try:
            # Sanitize metadata for ChromaDB (no None or nested complex dicts)
            sanitized_metadatas = []
            for meta in metadatas:
                clean = {}
                for k, v in meta.items():
                    if v is None:
                        clean[k] = ""
                    elif isinstance(v, (str, int, float, bool)):
                        clean[k] = v
                    else:
                        clean[k] = str(v)
                sanitized_metadatas.append(clean)

            self.collection.upsert(
                ids=ids,
                embeddings=vectors,
                documents=documents,
                metadatas=sanitized_metadatas,
            )
            logger.info(f"Successfully upserted {len(ids)} vectors into ChromaDB")
        except Exception as e:
            logger.error(f"Error upserting vectors to ChromaDB: {e}")
            raise StorageException(f"Vector store upsert failed: {str(e)}")

    def query(
        self,
        query_vector: List[float],
        top_k: int = 4,
    ) -> List[VectorQueryResult]:
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            parsed_results: List[VectorQueryResult] = []
            if not results or not results["ids"] or not results["ids"][0]:
                return parsed_results

            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                parsed_results.append(
                    VectorQueryResult(
                        id=ids[i],
                        text=docs[i] or "",
                        distance=float(distances[i]),
                        metadata=metas[i] or {},
                    )
                )

            return parsed_results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise StorageException(f"Vector store query failed: {str(e)}")

    def delete_by_document_id(self, document_id: str) -> None:
        try:
            self.collection.delete(
                where={"doc_id": str(document_id)},
            )
            logger.info(f"Deleted vectors for document_id={document_id} from ChromaDB")
        except Exception as e:
            logger.error(f"Error deleting vectors for document_id={document_id}: {e}")
            raise StorageException(f"Vector store deletion failed: {str(e)}")


class QdrantVectorStore(BaseVectorStore):
    """Placeholder adapter for Qdrant compatibility."""
    def __init__(self):
        logger.info(f"Initialized QdrantVectorStore targeting {settings.QDRANT_URL}")

    def upsert(self, ids, vectors, documents, metadatas) -> None:
        raise NotImplementedError("Qdrant store is not configured for current deployment")

    def query(self, query_vector, top_k: int = 4) -> List[VectorQueryResult]:
        raise NotImplementedError("Qdrant store is not configured for current deployment")

    def delete_by_document_id(self, document_id: str) -> None:
        raise NotImplementedError("Qdrant store is not configured for current deployment")


class PgVectorStore(BaseVectorStore):
    """Placeholder adapter for Pgvector compatibility."""
    def __init__(self):
        logger.info("Initialized PgVectorStore")

    def upsert(self, ids, vectors, documents, metadatas) -> None:
        raise NotImplementedError("Pgvector store is not configured for current deployment")

    def query(self, query_vector, top_k: int = 4) -> List[VectorQueryResult]:
        raise NotImplementedError("Pgvector store is not configured for current deployment")

    def delete_by_document_id(self, document_id: str) -> None:
        raise NotImplementedError("Pgvector store is not configured for current deployment")


def get_vector_store() -> BaseVectorStore:
    """Factory selecting the vector store backend based on settings.VECTOR_DB."""
    db_choice = settings.VECTOR_DB.lower()
    if db_choice == "chromadb":
        return ChromaVectorStore()
    elif db_choice == "qdrant":
        return QdrantVectorStore()
    elif db_choice == "pgvector":
        return PgVectorStore()
    else:
        raise StorageException(f"Unsupported VECTOR_DB choice: {settings.VECTOR_DB}")


# Singleton instance
vector_store = get_vector_store()
