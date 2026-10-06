import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.config import settings

COLLECTION_NAME = "eduvault_knowledge_base"


class VectorStoreService:
    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        if settings.CHROMA_HOST:
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
        else:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

        # Default fast embedding function
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_fn,
        )

    def add_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0

        ids = [f"{document_id}_{chunk['chunk_index']}" for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            meta = chunk.get("metadata", {}).copy()
            meta["document_id"] = document_id
            meta["chunk_index"] = chunk["chunk_index"]
            # Chroma requires string/int/float/bool in metadata
            cleaned_meta = {
                k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                for k, v in meta.items()
            }
            metadatas.append(cleaned_meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
        )

        candidates = []
        if not results or not results["documents"] or not results["documents"][0]:
            return candidates

        docs = results["documents"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(docs)

        for doc, dist, meta in zip(docs, distances, metadatas):
            # For cosine distance, similarity is 1.0 - distance
            similarity = 1.0 - dist if dist is not None else 1.0
            candidates.append({
                "content": doc,
                "distance": dist,
                "similarity": round(float(similarity), 4),
                "metadata": meta,
            })

        return candidates

    def delete_document(self, document_id: str):
        self.collection.delete(where={"document_id": document_id})


vector_store = VectorStoreService()
