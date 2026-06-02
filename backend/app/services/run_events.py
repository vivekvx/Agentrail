from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RunEvent


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
