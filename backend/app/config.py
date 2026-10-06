<<<<<<< HEAD
from typing import List, Union
from pydantic import field_validator
=======
from typing import Literal
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
<<<<<<< HEAD
    # App
    APP_ENV: str = "production"
    PORT: int = 8000
    SECRET_KEY: str = "eduvault-secret-super-secure-key-change-in-prod"
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "https://*.vercel.app",
        "*"
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduvault.db"

    # Vector DB
    VECTOR_DB: str = "chromadb"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    CHROMA_HOST: str = ""
    CHROMA_PORT: int = 8001

    # LLM & Embeddings
    LLM_PROVIDER: str = "gemini"  # gemini | groq
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # RAG Guardrails
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35

    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    UPLOAD_DIR: str = "./uploads"

=======
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

<<<<<<< HEAD
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v:
            return "sqlite+aiosqlite:///./eduvault.db"
        # Render PostgreSQL URL fixes (postgres:// -> postgresql+asyncpg://)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
=======
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
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070


settings = Settings()
