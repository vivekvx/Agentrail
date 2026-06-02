from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    repo_path: str = Field(min_length=1, max_length=2048)
    user_task: str = Field(min_length=1)


class RunRead(BaseModel):
    id: int
    repo_path: str
    user_task: str
    status: str
    final_report: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunStartResponse(BaseModel):
    id: int
    status: str
    has_final_report: bool
    final_report: str | None
    error_message: str | None
