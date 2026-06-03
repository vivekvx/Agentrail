from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_task: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="created")
    current_node: Mapped[str | None] = mapped_column(String(128), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fix_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    patch_diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
