from __future__ import annotations

import asyncio
import json
import json as _json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RunEvent

if TYPE_CHECKING:
    pass


def log_run_event(
    db: Session,
    run_id: int,
    event_type: str,
    title: str,
    message: str | None = None,
    payload: dict[str, object] | None = None,
) -> RunEvent:
    event = RunEvent(
        run_id=run_id,
        event_type=event_type,
        title=title,
        message=message,
        payload_json=json.dumps(payload) if payload is not None else None,
    )
    db.add(event)
    db.flush()
    return event


def list_run_events(db: Session, run_id: int) -> list[RunEvent]:
    statement = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.created_at.asc(), RunEvent.id.asc())
    )
    return list(db.scalars(statement).all())


async def stream_run_events(
    run_id: int, db_factory: Callable[[], Session]
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events by polling the DB for new RunEvent rows."""
    last_id = 0
    terminal_statuses = {"completed", "failed", "rejected"}

    while True:
        db = db_factory()
        try:
            stmt = (
                select(RunEvent)
                .where(RunEvent.run_id == run_id, RunEvent.id > last_id)
                .order_by(RunEvent.id.asc())
            )
            new_events = list(db.scalars(stmt).all())
        finally:
            db.close()

        for event in new_events:
            payload = {
                "id": event.id,
                "event_type": event.event_type,
                "title": event.title,
                "message": event.message,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "payload": _json.loads(event.payload_json) if event.payload_json else None,
            }
            last_id = event.id
            yield f"data: {_json.dumps(payload)}\n\n"

        # Check if run reached terminal state
        db = db_factory()
        try:
            from app.db.models import AgentRun

            run = db.get(AgentRun, run_id)
            if run and run.status in terminal_statuses:
                yield 'data: {"event_type": "stream_end"}\n\n'
                return
        finally:
            db.close()

        await asyncio.sleep(1.0)
