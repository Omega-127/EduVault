from typing import List, Optional

from app.config import settings
from app.core.logging import logger
from app.ingestion.embedder import embedder
from app.storage.vector_store import EmptyVectorStore, VectorQueryResult, vector_store


class RAGRetriever:
    """Retrieves institutional knowledge chunks using dense vector similarity with safety gating."""

    def __init__(
        self,
        top_k: int = settings.RETRIEVAL_TOP_K,
        threshold: float = settings.SIMILARITY_THRESHOLD,
    ):
        self.top_k = top_k
        self.threshold = threshold

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Optional[List[VectorQueryResult]]:
        k = top_k if top_k is not None else self.top_k
        thresh = threshold if threshold is not None else self.threshold

        # Avoid loading the embedding model when the vector DB is unavailable
        if isinstance(vector_store, EmptyVectorStore):
            logger.info("Retriever skipped: EmptyVectorStore has no indexed chunks.")
            return None

        # Step 1: Embed query
        query_vector = embedder.embed_query(query)

        # Step 2: Query vector database
        results = vector_store.query(query_vector=query_vector, top_k=k)

        if not results:
            logger.info("Retriever found 0 vector matches.")
            return None

        # Step 3: Safety gate check against top match
        best_distance = results[0].distance
        logger.info(f"Top result distance: {best_distance:.4f} (Threshold: {thresh:.4f})")

        if best_distance > thresh:
            logger.info(
                f"Best vector distance ({best_distance:.4f}) exceeds threshold ({thresh:.4f}). Triggering safety gate fallback."
            )
            return None

        # Step 4: Filter remaining matches below threshold
        valid_chunks = [r for r in results if r.distance <= thresh]
        return valid_chunks


retriever = RAGRetriever()
