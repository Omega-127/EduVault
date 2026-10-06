<<<<<<< HEAD
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.db.base import Base

# Engine configuration
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.APP_ENV == "development"),
    future=True,
    connect_args=connect_args,
=======
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create async engine for PostgreSQL (or SQLite for testing/fallback if configured)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
<<<<<<< HEAD
    autocommit=False,
=======
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    autoflush=False,
)


<<<<<<< HEAD
async def init_db():
    """Create all tables in the database if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
=======
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
