"""Application configuration, loaded from environment / module constants."""

from dataclasses import dataclass, field


@dataclass
class Settings:
    """Central configuration for the backend application."""

    # -- Server ----------------------------------------------------------------
    app_name: str = "Personal Blog"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # -- Database --------------------------------------------------------------
    db_url: str = "sqlite+aiosqlite:///./data/blog.db"
    db_dir: str = "./data"

    # -- Uploads ---------------------------------------------------------------
    upload_dir: str = "./uploads"

    # -- Auth ------------------------------------------------------------------
    secret_key: str = "dev-secret-change-in-production-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # -- CORS ------------------------------------------------------------------
    cors_origins: list = field(default_factory=lambda: ["*"])

    # -- Password policy -------------------------------------------------------
    min_password_length: int = 8

    @property
    def access_expire_delta(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def refresh_expire_delta(self) -> int:
        return self.refresh_token_expire_days * 86400


settings = Settings()