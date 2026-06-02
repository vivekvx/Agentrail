from __future__ import annotations

import json
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents.graph import build_agent_graph
from app.db.models import AgentRun, RunEvent
from app.db.session import get_db
from app.schemas.runs import ApprovalResponse, RunCreate, RunEventRead, RunRead, RunStartResponse
from app.services.run_events import list_run_events, log_run_event
from app.tools.path_policy import validate_repo_directory


router = APIRouter(prefix="/api/runs", tags=["runs"])
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])/(?:[^/\s:]+/)*[^/\s:]+")


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> RunRead:
    try:
        repo_path = validate_repo_directory(payload.repo_path)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_sanitize_error_message(str(exc)),
        ) from exc

    run = AgentRun(
        repo_path=str(repo_path),
        user_task=payload.user_task,
        expected_behavior=payload.expected_behavior,
        test_command=payload.test_command,
        status="created",
        thread_id=str(uuid4()),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    log_run_event(
        db,
        run.id,
        "run_created",
        "Run created",
        payload={
            "status": run.status,
            "repo_path": run.repo_path,
            "test_command": run.test_command,
        },
    )
    db.commit()
    return _run_read(run)


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunRead:
    return _run_read(_get_run_or_404(run_id, db))


@router.post("/{run_id}/start", response_model=RunStartResponse)
def start_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    run = _get_run_or_404(run_id, db)

    run.status = "running"
    run.current_node = "planner"
    run.approval_payload = None
    run.approval_status = None
    run.patch_diff = None
    run.test_result = None
    run.verification_result = None
    run.risk_score = None
    run.final_report = None
    run.error_message = None
    log_run_event(
        db,
        run.id,
        "run_started",
        "Run started",
        payload={"status": run.status},
    )
    db.commit()
    db.refresh(run)

    try:
        repo_path = validate_repo_directory(run.repo_path)
        graph = build_agent_graph()
        result = graph.invoke(
            {
                "repo_path": str(repo_path),
                "user_task": run.user_task,
                "expected_behavior": run.expected_behavior,
                "test_command": run.test_command,
            },
            config=_thread_config(run),
        )
        _persist_graph_result(run, result)
        interrupt_payload = _extract_interrupt_payload(result)
        if interrupt_payload is not None:
            run.status = "pending_approval"
            run.current_node = "approval_node"
            run.approval_payload = json.dumps(interrupt_payload)
            run.error_message = None
            _log_graph_state_events(db, run, result)
            log_run_event(
                db,
                run.id,
                "pending_approval",
                "Run is waiting for approval",
                payload={
                    "approval_payload": interrupt_payload,
                    "patch_diff": run.patch_diff,
                },
            )
            db.commit()
            db.refresh(run)
            return _run_start_response(run)

        final_report = result.get("final_report")
        if not isinstance(final_report, str):
            raise RuntimeError("Graph did not produce a final report")
    except Exception as exc:
        run.status = "failed"
        run.current_node = "error"
        run.error_message = _sanitize_error_message(str(exc))
        log_run_event(
            db,
            run.id,
            "run_failed",
            "Run failed",
            message=run.error_message,
            payload={"status": run.status},
        )
        db.commit()
        db.refresh(run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph execution failed.",
        ) from exc

    run.status = "completed"
    run.current_node = "reporter"
    run.final_report = final_report
    run.approval_payload = None
    run.error_message = None
    _log_graph_state_events(db, run, result)
    _log_completion_events(db, run)
    db.commit()
    db.refresh(run)

    return _run_start_response(run)


@router.get("/{run_id}/approval", response_model=ApprovalResponse)
def get_approval(run_id: int, db: Session = Depends(get_db)) -> ApprovalResponse:
    run = _get_run_or_404(run_id, db)
    return ApprovalResponse(
        id=run.id,
        status=run.status,
        approval_payload=_load_approval_payload(run),
    )


@router.get("/{run_id}/events", response_model=list[RunEventRead])
def get_run_events(run_id: int, db: Session = Depends(get_db)) -> list[RunEventRead]:
    _get_run_or_404(run_id, db)
    return [_run_event_read(event) for event in list_run_events(db, run_id)]


@router.post("/{run_id}/approve", response_model=RunStartResponse)
def approve_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    return _resume_run(run_id, "approve", "completed", db)


@router.post("/{run_id}/reject", response_model=RunStartResponse)
def reject_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    return _resume_run(run_id, "reject", "rejected", db)


def _resume_run(
    run_id: int,
    decision: str,
    completed_status: str,
    db: Session,
) -> RunStartResponse:
    run = _get_run_or_404(run_id, db)
    if run.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run is not waiting for approval",
        )

    run.status = "running"
    run.current_node = "test_runner" if decision == "approve" else "reporter"
    run.error_message = None
    log_run_event(
        db,
        run.id,
        "approved" if decision == "approve" else "rejected",
        "Patch approved" if decision == "approve" else "Patch rejected",
        payload={"decision": decision},
    )
    db.commit()
    db.refresh(run)

    try:
        graph = build_agent_graph()
        result = graph.invoke(Command(resume=decision), config=_thread_config(run))
        _persist_graph_result(run, result)
        final_report = result.get("final_report")
        if not isinstance(final_report, str):
            raise RuntimeError("Graph did not produce a final report")
    except Exception as exc:
        run.status = "failed"
        run.current_node = "error"
        run.error_message = _sanitize_error_message(str(exc))
        log_run_event(
            db,
            run.id,
            "run_failed",
            "Run failed",
            message=run.error_message,
            payload={"status": run.status},
        )
        db.commit()
        db.refresh(run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph execution failed.",
        ) from exc

    run.status = completed_status
    run.current_node = "reporter"
    run.final_report = final_report
    run.error_message = None
    _log_graph_state_events(db, run, result)
    _log_completion_events(db, run)
    db.commit()
    db.refresh(run)

    return _run_start_response(run)


def _get_run_or_404(run_id: int, db: Session) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run


def _thread_config(run: AgentRun) -> dict[str, dict[str, str]]:
    thread_id = run.thread_id or str(run.id)
    return {"configurable": {"thread_id": thread_id}}


def _extract_interrupt_payload(result: dict[str, object]) -> dict[str, object] | None:
    interrupts = result.get("__interrupt__")
    if not isinstance(interrupts, list) or not interrupts:
        return None

    value = getattr(interrupts[0], "value", None)
    if isinstance(value, dict):
        return value
    return None


def _load_approval_payload(run: AgentRun) -> dict[str, object] | None:
    loaded = _load_json_dict(run.approval_payload)
    if isinstance(loaded, dict):
        return loaded
    return None


def _load_json_dict(value: str | None) -> dict[str, object] | None:
    if value is None:
        return None
    loaded = json.loads(value)
    if isinstance(loaded, dict):
        return loaded
    return None


def _dump_json(value: object | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _persist_graph_result(run: AgentRun, result: dict[str, object]) -> None:
    run.patch_diff = _string_or_none(result.get("patch_diff"))
    run.approval_status = _string_or_none(result.get("approval_status"))
    run.final_report = _string_or_none(result.get("final_report"))
    run.test_result = _dump_json(_dict_or_none(result.get("test_result")))
    run.verification_result = _dump_json(_dict_or_none(result.get("verification_result")))
    run.risk_score = _dump_json(_dict_or_none(result.get("risk_score")))


def _run_read(run: AgentRun) -> RunRead:
    return RunRead(
        id=run.id,
        repo_path=run.repo_path,
        user_task=run.user_task,
        expected_behavior=run.expected_behavior,
        test_command=run.test_command,
        status=run.status,
        current_node=run.current_node,
        final_report=run.final_report,
        approval_payload=_load_json_dict(run.approval_payload),
        approval_status=run.approval_status,
        patch_diff=run.patch_diff,
        test_result=_load_json_dict(run.test_result),
        verification_result=_load_json_dict(run.verification_result),
        risk_score=_load_json_dict(run.risk_score),
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _run_start_response(run: AgentRun) -> RunStartResponse:
    return RunStartResponse(
        id=run.id,
        status=run.status,
        current_node=run.current_node,
        has_final_report=run.final_report is not None,
        final_report=run.final_report,
        approval_status=run.approval_status,
        patch_diff=run.patch_diff,
        test_result=_load_json_dict(run.test_result),
        verification_result=_load_json_dict(run.verification_result),
        risk_score=_load_json_dict(run.risk_score),
        error_message=run.error_message,
        approval_payload=_load_json_dict(run.approval_payload),
    )


def _run_event_read(event: RunEvent) -> RunEventRead:
    return RunEventRead(
        id=event.id,
        run_id=event.run_id,
        event_type=event.event_type,
        title=event.title,
        message=event.message,
        payload=_load_json_dict(event.payload_json),
        created_at=event.created_at,
    )


def _dict_or_none(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _sanitize_error_message(message: str) -> str:
    sanitized = message.strip().splitlines()[0]
    sanitized = ABSOLUTE_PATH_PATTERN.sub("[path]", sanitized)
    if sanitized.startswith("Repository path does not exist:"):
        return "Repository path does not exist."
    if sanitized.startswith("Repository path is not a directory:"):
        return "Repository path is not a directory."
    if sanitized.startswith("Repository path is outside allowed roots:"):
        return "Repository path is outside allowed roots."
    return sanitized.replace("Traceback", "").strip() or "Unexpected error."


def _log_graph_state_events(db: Session, run: AgentRun, result: dict[str, object]) -> None:
    repo_scan = _dict_or_none(result.get("repo_scan"))
    if repo_scan is not None:
        log_run_event(
            db,
            run.id,
            "repo_scanned",
            "Repository scanned",
            payload={
                "detected_stack": repo_scan.get("detected_stack"),
                "probable_backend_directory": repo_scan.get("probable_backend_directory"),
                "probable_frontend_directory": repo_scan.get("probable_frontend_directory"),
            },
        )

    search_results = result.get("search_results")
    if isinstance(search_results, list):
        log_run_event(
            db,
            run.id,
            "code_searched",
            "Code search completed",
            payload={"match_count": len(search_results)},
        )

    evidence = result.get("evidence")
    if isinstance(evidence, list):
        log_run_event(
            db,
            run.id,
            "evidence_read",
            "Evidence gathered",
            payload={"evidence_count": len(evidence)},
        )

    root_cause = _string_or_none(result.get("root_cause"))
    if root_cause:
        log_run_event(
            db,
            run.id,
            "root_cause_generated",
            "Root cause generated",
            message=root_cause,
        )

    if run.patch_diff:
        log_run_event(
            db,
            run.id,
            "patch_generated",
            "Patch preview generated",
            payload={"patch_diff": run.patch_diff},
        )

    test_result = _load_json_dict(run.test_result)
    if test_result is not None:
        log_run_event(
            db,
            run.id,
            "tests_run",
            "Tests completed",
            payload=test_result,
        )

    verification_result = _load_json_dict(run.verification_result)
    if verification_result is not None:
        log_run_event(
            db,
            run.id,
            "verified",
            "Verification result recorded",
            payload=verification_result,
        )

    risk_score = _load_json_dict(run.risk_score)
    if risk_score is not None:
        log_run_event(
            db,
            run.id,
            "risk_scored",
            "Risk score recorded",
            payload=risk_score,
        )


def _log_completion_events(db: Session, run: AgentRun) -> None:
    if run.final_report:
        log_run_event(
            db,
            run.id,
            "report_generated",
            "Final report generated",
            payload={"status": run.status},
        )
    if run.status == "completed":
        log_run_event(
            db,
            run.id,
            "run_completed",
            "Run completed",
            payload={"status": run.status},
        )
