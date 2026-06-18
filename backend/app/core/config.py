from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-change-in-production"

logger = logging.getLogger("agentrail.config")


class Settings(BaseSettings):
    environment: str = Field(default="development", validation_alias="ENV")
    database_url: str = "sqlite:///./agentrail.db"
    secret_key: str = _DEV_SECRET
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"

    # Observability + CORS
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"  # comma-separated

    # Repo scanning
    repo_workspace_dir: str = "./data/repos"
    git_clone_timeout_seconds: int = 60
    max_repo_files: int = 20000
    # DoS hardening
    max_repo_size_kb: int = 200_000  # reject repos larger than ~200 MB before clone
    max_concurrent_scans: int = 2  # cap simultaneous clones
    scan_rate_limit: str = "10/hour"  # per-IP limit on imports
    github_api_timeout_seconds: int = 10

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @field_validator("algorithm")
    @classmethod
    def _restrict_algorithm(cls, v: str) -> str:
        if v not in {"HS256", "HS384", "HS512"}:
            raise ValueError("algorithm must be HS256, HS384, or HS512")
        return v

    @model_validator(mode="after")
    def _enforce_secret_key(self) -> "Settings":
        if len(self.secret_key) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        if self.secret_key == _DEV_SECRET:
            if self.is_production:
                raise ValueError(
                    "SECRET_KEY must be changed from its default in production "
                    "(ENV=production). Generate one: "
                    'python -c "import secrets; print(secrets.token_hex(32))"'
                )
            logger.warning(
                "SECRET_KEY is using the insecure default. Set SECRET_KEY before deploying."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
