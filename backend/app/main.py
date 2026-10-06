from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD
from sqlalchemy.future import select
from app.config import settings
from app.db.session import init_db, AsyncSessionLocal
from app.db.models.user import User
from app.core.security import get_password_hash
from app.api.v1.router import api_v1_router
=======
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.storage.object_store import object_store
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070


@asynccontextmanager
async def lifespan(app: FastAPI):
<<<<<<< HEAD
    # Startup: Initialize tables
    await init_db()

    # Seed default admin if missing
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@eduvault.edu"))
        existing_admin = result.scalar_one_or_none()
        if not existing_admin:
            default_admin = User(
                email="admin@eduvault.edu",
                hashed_password=get_password_hash("Admin@123"),
                role="admin",
                is_active=True,
            )
            session.add(default_admin)
            await session.commit()

    yield


app = FastAPI(
    title="EduVault API",
    description="AI-Powered University Knowledge & Document Assistant Backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
=======
    """Application lifespan context for startup and shutdown routines."""
    logger.info("Initializing EduVault application...")
    try:
        # Ensure object storage bucket is created on startup if reachable
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV != "production" else ["http://localhost:3000", "http://127.0.0.1:3000"],
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Mount API Routers
app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "EduVault API",
        "version": "0.1.0",
        "env": settings.APP_ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
=======
# 2. Trusted Host Middleware in production
if settings.APP_ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "backend"],
    )

# 3. Global Exception Handlers
register_exception_handlers(app)

# 4. API Routers
app.include_router(api_v1_router)


# 5. Health Check Endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Application Health Check",
)
async def health_check():
    """Returns the operational status of the service."""
    return {"status": "ok"}
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
