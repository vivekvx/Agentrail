from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunCreate(BaseModel):
    repo_path: str | None = Field(default=None, min_length=1, max_length=2048)
    repo_url: str | None = Field(default=None, min_length=1, max_length=2048)
    user_task: str = Field(min_length=1)
    expected_behavior: str | None = None
    test_command: str | None = None

    @model_validator(mode="after")
    def validate_repo_source(self) -> "RunCreate":
        if self.repo_path and self.repo_url:
            raise ValueError("Provide either repo_path or repo_url, not both.")
        if not self.repo_path and not self.repo_url:
            raise ValueError("Either repo_path or repo_url is required.")
        return self


class RunRead(BaseModel):
    id: int
    repo_path: str | None
    repo_url: str | None
    user_task: str
    expected_behavior: str | None
    test_command: str | None
    status: str
    current_node: str | None
    approval_payload: dict[str, object] | None
    approval_status: str | None
    fix_strategy: dict[str, object] | None
    patch_diff: str | None
    test_result: dict[str, object] | None
    verification_result: dict[str, object] | None
    risk_score: dict[str, object] | None
    final_report: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict()


class RunStartResponse(BaseModel):
    id: int
    status: str
    current_node: str | None
    has_final_report: bool
    repo_path: str | None = None
    repo_url: str | None = None
    final_report: str | None
    approval_status: str | None
    fix_strategy: dict[str, object] | None = None
    patch_diff: str | None
    test_result: dict[str, object] | None = None
    verification_result: dict[str, object] | None = None
    risk_score: dict[str, object] | None = None
    error_message: str | None
    approval_payload: dict[str, object] | None = None


class ApprovalResponse(BaseModel):
    id: int
    status: str
    approval_payload: dict[str, object] | None


class RunEventRead(BaseModel):
    id: int
    run_id: int
    event_type: str
    title: str
    message: str | None
    payload: dict[str, object] | None
    created_at: datetime
