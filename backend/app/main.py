from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from app.config import settings
from app.db.session import init_db, AsyncSessionLocal
from app.db.models.user import User
from app.core.security import get_password_hash
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
