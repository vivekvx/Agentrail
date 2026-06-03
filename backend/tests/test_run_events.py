from __future__ import annotations

import json

from app.db.models import AgentRun
from app.db.session import Base, SessionLocal, engine
from app.services.run_events import list_run_events, log_run_event


def _reset_tables() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_list_run_events_returns_events_in_creation_order() -> None:
    _reset_tables()
    with SessionLocal() as db:
        run = AgentRun(
            repo_path="/tmp/repo",
            repo_url=None,
            user_task="Inspect auth issue",
            status="created",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        log_run_event(db, run.id, "run_created", "Run created", payload={"step": 1})
        log_run_event(db, run.id, "run_started", "Run started", payload={"step": 2})
        db.commit()

        events = list_run_events(db, run.id)

    assert [event.event_type for event in events] == ["run_created", "run_started"]


def test_run_event_payloads_are_json_safe() -> None:
    _reset_tables()
    payload = {"status": "pending_approval", "evidence_count": 2}

    with SessionLocal() as db:
        run = AgentRun(
            repo_path="/tmp/repo",
            repo_url=None,
            user_task="Inspect auth issue",
            status="created",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        event = log_run_event(
            db,
            run.id,
            "pending_approval",
            "Run is waiting for approval",
            payload=payload,
        )
        db.commit()
        db.refresh(event)

        stored_payload = json.loads(event.payload_json or "null")

    assert stored_payload == payload
