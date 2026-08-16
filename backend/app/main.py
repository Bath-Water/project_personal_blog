"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.config import settings
from app.database import close_engine, init_db
from app.middleware.cors import install_cors

# Ensure runtime directories exist.
Path(settings.db_dir).mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: create DB tables on startup, dispose engine on shutdown."""
    await init_db()
    yield
    await close_engine()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# Install permissive CORS middleware (allow all origins in development).
install_cors(app)

# Include routers.
from app.routers import auth, categories, comments, media, posts, search, settings as stg  # noqa: E402
from app.routers import tags as tags_router  # noqa: E402

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(media.router)
app.include_router(categories.router)
app.include_router(tags_router.router)
app.include_router(comments.router)
app.include_router(search.router)
app.include_router(stg.router)


@app.get("/api/health")
async def health():
    """Liveness probe."""
    return {"code": 0, "data": {"status": "ok"}, "message": "ok"}