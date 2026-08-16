"""CORS middleware helper."""

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def install_cors(app) -> None:
    """Install permissive CORS middleware on *app*."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )