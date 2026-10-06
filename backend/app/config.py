from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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


settings = Settings()
