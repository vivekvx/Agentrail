from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-change-in-production"


class Settings(BaseSettings):
    # SQLite fallback for local dev: sqlite:///./agentrail.db
    database_url: str = "postgresql+psycopg2://agentrail:agentrail@localhost:5432/agentrail"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    llm_root_cause_enabled: bool = False
    llm_fix_strategy_enabled: bool = False
    llm_timeout_seconds: int = 30
    repo_workspace_dir: str = "./data/repos"
    github_import_enabled: bool = True
    github_issue_import_enabled: bool = True
    github_api_timeout_seconds: int = 30
    git_clone_timeout_seconds: int = 60
    max_repo_size_mb: int = 100
    github_token: str | None = None
    max_issue_body_chars: int = 12000
    e2b_enabled: bool = False
    e2b_api_key: str | None = None
    e2b_template: str | None = None
    e2b_timeout_seconds: int = 120
    e2b_run_tests_after_approval: bool = False
    sandbox_runner_provider: str = "local"
    max_sandbox_upload_mb: int = 50
    secret_key: str = _DEV_SECRET
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"

    @field_validator("secret_key")
    @classmethod
    def _require_strong_key(cls, v: str) -> str:
        if v == _DEV_SECRET:
            import logging, os
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
