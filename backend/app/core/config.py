from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./agentrail.db"
    openai_api_key: str | None = None
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
