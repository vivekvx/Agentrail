from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.graph import build_agent_graph
from app.db.models import AgentRun
from app.db.session import get_db
from app.schemas.runs import RunCreate, RunRead, RunStartResponse
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
    run.error_message = None
    db.commit()
    db.refresh(run)

    return RunStartResponse(
        id=run.id,
        status=run.status,
        has_final_report=run.final_report is not None,
        final_report=run.final_report,
        error_message=run.error_message,
    )
