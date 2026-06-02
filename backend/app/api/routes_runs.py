from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents.graph import build_agent_graph
from app.db.models import AgentRun
from app.db.session import get_db
from app.schemas.runs import ApprovalResponse, RunCreate, RunRead, RunStartResponse
from app.tools.path_policy import validate_repo_directory


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> AgentRun:
    try:
        repo_path = validate_repo_directory(payload.repo_path)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    run = AgentRun(
        repo_path=str(repo_path),
        user_task=payload.user_task,
        status="created",
        thread_id=str(uuid4()),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, db: Session = Depends(get_db)) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run


@router.post("/{run_id}/start", response_model=RunStartResponse)
def start_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    run.status = "running"
    run.approval_payload = None
    run.final_report = None
    run.error_message = None
    db.commit()
    db.refresh(run)

    try:
        repo_path = validate_repo_directory(run.repo_path)
        graph = build_agent_graph()
        result = graph.invoke(
            {
                "repo_path": str(repo_path),
                "user_task": run.user_task,
            },
            config=_thread_config(run),
        )
        interrupt_payload = _extract_interrupt_payload(result)
        if interrupt_payload is not None:
            run.status = "pending_approval"
            run.approval_payload = json.dumps(interrupt_payload)
            run.error_message = None
            db.commit()
            db.refresh(run)
            return RunStartResponse(
                id=run.id,
                status=run.status,
                has_final_report=False,
                final_report=None,
                error_message=None,
                approval_payload=interrupt_payload,
            )

        final_report = result.get("final_report")
        if not isinstance(final_report, str):
            raise RuntimeError("Graph did not produce a final report")
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        db.commit()
        db.refresh(run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed: {run.error_message}",
        ) from exc

    run.status = "completed"
    run.final_report = final_report
    run.approval_payload = None
    run.error_message = None
    db.commit()
    db.refresh(run)

    return RunStartResponse(
        id=run.id,
        status=run.status,
        has_final_report=run.final_report is not None,
        final_report=run.final_report,
        error_message=run.error_message,
        approval_payload=None,
    )


@router.get("/{run_id}/approval", response_model=ApprovalResponse)
def get_approval(run_id: int, db: Session = Depends(get_db)) -> ApprovalResponse:
    run = _get_run_or_404(run_id, db)
    return ApprovalResponse(
        id=run.id,
        status=run.status,
        approval_payload=_load_approval_payload(run),
    )


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
    run.error_message = None
    db.commit()
    db.refresh(run)

    try:
        graph = build_agent_graph()
        result = graph.invoke(Command(resume=decision), config=_thread_config(run))
        final_report = result.get("final_report")
        if not isinstance(final_report, str):
            raise RuntimeError("Graph did not produce a final report")
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        db.commit()
        db.refresh(run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed: {run.error_message}",
        ) from exc

    run.status = completed_status
    run.final_report = final_report
    run.error_message = None
    db.commit()
    db.refresh(run)

    return RunStartResponse(
        id=run.id,
        status=run.status,
        has_final_report=run.final_report is not None,
        final_report=run.final_report,
        error_message=run.error_message,
        approval_payload=_load_approval_payload(run),
    )


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
    if run.approval_payload is None:
        return None
    loaded = json.loads(run.approval_payload)
    if isinstance(loaded, dict):
        return loaded
    return None
