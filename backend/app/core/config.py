from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-change-in-production"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./agentrail.db"
    secret_key: str = _DEV_SECRET
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"

    # Repo scanning
    repo_workspace_dir: str = "./data/repos"
    git_clone_timeout_seconds: int = 60
    max_repo_files: int = 20000

    @field_validator("secret_key")
    @classmethod
    def _require_strong_key(cls, v: str) -> str:
        if v == _DEV_SECRET:
            import logging
            import os
            if os.getenv("ENV", "development") == "production":
                raise ValueError("SECRET_KEY must be changed from its default in production")
            logging.warning("SECRET_KEY is using the insecure default. Set SECRET_KEY env var before deploying.")
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return v

    @field_validator("algorithm")
    @classmethod
    def _restrict_algorithm(cls, v: str) -> str:
        if v not in {"HS256", "HS384", "HS512"}:
            raise ValueError("algorithm must be HS256, HS384, or HS512")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
