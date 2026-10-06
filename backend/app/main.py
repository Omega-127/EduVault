from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.storage.object_store import object_store


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
