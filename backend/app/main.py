from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models.user import User
from app.db.session import engine, AsyncSessionLocal
from app.storage.object_store import object_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info("Initializing EduVault application...")

    # 1. Initialize DB tables if they don't exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.warning(f"Could not verify database schema during startup: {e}")

    # 2. Seed default admin account if none exists
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == "admin@eduvault.edu")
            )
            admin_user = result.scalar_one_or_none()
            if not admin_user:
                default_admin = User(
                    email="admin@eduvault.edu",
                    hashed_pw=get_password_hash("Admin@123"),
                    role="admin",
                    is_active=True,
                )
                session.add(default_admin)
                await session.commit()
                logger.info("Default admin created: admin@eduvault.edu / Admin@123")
    except Exception as e:
        logger.warning(f"Could not seed admin user: {e}")

    # 3. Ensure object storage bucket is created if reachable
    try:
        object_store.ensure_bucket_exists()
    except Exception as e:
        logger.warning(f"Could not initialize object store during startup: {e}")

    yield

    logger.info("EduVault application shutting down...")


app = FastAPI(
    title="EduVault API",
    description="AI-Powered University Knowledge & Document Assistant backend providing grounded RAG Q&A with explicit citations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 1. CORS Middleware
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Global Exception Handlers
register_exception_handlers(app)

# 3. API Routers
app.include_router(api_v1_router)


# 4. Health Check Endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Application Health Check",
)
async def health_check():
    """Returns the operational status of the service."""
    return {
        "status": "ok",
        "app": "EduVault API",
        "env": settings.APP_ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
