from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "eduvault-secret-key-change-in-production-min-32-chars-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduvault"

    # Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "eduvault-docs"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector DB
    VECTOR_DB: Literal["chromadb", "qdrant", "pgvector"] = "chromadb"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    QDRANT_URL: str = "http://localhost:6333"

    # Embeddings
    EMBEDDING_MODEL: Literal["all-MiniLM-L6-v2", "gemini"] = "all-MiniLM-L6-v2"

    # LLM
    LLM_PROVIDER: Literal["gemini", "groq"] = "gemini"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # RAG
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35


settings = Settings()
