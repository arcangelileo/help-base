"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    model_config = {"env_prefix": "HELPBASE_", "env_file": ".env", "extra": "ignore"}

    # App
    app_name: str = "HelpBase"
    debug: bool = False
    secret_key: str = "change-me-in-production-please"
    base_url: str = "http://localhost:8000"

    # Database
    database_url: str = f"sqlite+aiosqlite:///{Path.cwd()}/helpbase.db"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


settings = Settings()
