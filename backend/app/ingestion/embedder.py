from typing import List, Optional
import numpy as np

from app.config import settings
from app.core.exceptions import IngestionException
from app.core.logging import logger


class Embedder:
    """Batch embedding service supporting all-MiniLM-L6-v2 and Gemini."""

    def __init__(self):
        self._local_model = None
        self.model_name = settings.EMBEDDING_MODEL

    def _get_local_model(self):
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2...")
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        return self._local_model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text documents."""
        if not texts:
            return []

        if self.model_name == "all-MiniLM-L6-v2":
            model = self._get_local_model()
            embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
            return embeddings.tolist()
        elif self.model_name == "gemini":
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                raise IngestionException("GEMINI_API_KEY is not configured for Gemini embeddings")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Gemini batch embedding
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document",
                )
                embeddings.append(result["embedding"])
            return embeddings
        else:
            raise IngestionException(f"Unsupported embedding model: {self.model_name}")

    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a single search query."""
        if self.model_name == "all-MiniLM-L6-v2":
            model = self._get_local_model()
            embedding = model.encode(query, show_progress_bar=False)
            return embedding.tolist()
        elif self.model_name == "gemini":
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                raise IngestionException("GEMINI_API_KEY is not configured for Gemini embeddings")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
        else:
            raise IngestionException(f"Unsupported embedding model: {self.model_name}")


embedder = Embedder()
