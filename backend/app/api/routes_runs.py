from __future__ import annotations

import json
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents.graph import build_agent_graph
from app.core.config import get_settings
from app.db.models import AgentRun, RunEvent
from app.db.session import get_db
from app.schemas.runs import ApprovalResponse, RunCreate, RunEventRead, RunRead, RunStartResponse
from app.services.github_issues import GitHubIssueFetchError, fetch_github_issue_context
from app.services.pr_draft import PRDraft, generate_pr_draft
from app.services.repo_importer import import_github_repository
from app.services.run_events import list_run_events, log_run_event
from app.tools.github_issue_url import validate_github_issue_url
from app.tools.github_url import validate_github_repo_url
from app.tools.path_policy import resolve_path
from app.tools.path_policy import validate_repo_directory
import concurrent.futures as _cf


router = APIRouter(prefix="/api/runs", tags=["runs"])
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])/(?:[^/\s:]+/)*[^/\s:]+")
TOKEN_PATTERN = re.compile(r"\b(?:ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b")


@router.get("", response_model=list[RunRead])
def list_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[RunRead]:
    runs = (
        db.query(AgentRun)
        .order_by(AgentRun.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [_run_read(run) for run in runs]


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> RunRead:
    repo_path: str | None = None
    repo_url: str | None = None
    issue_context: dict[str, object] | None = None
    issue_url: str | None = None
    user_task = payload.user_task.strip()
    expected_behavior = payload.expected_behavior

    if payload.repo_path:
        try:
            repo_path = str(validate_repo_directory(payload.repo_path))
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_sanitize_error_message(str(exc)),
            ) from exc

    if payload.issue_url:
        settings = get_settings()
        if not settings.github_issue_import_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub issue import is disabled.",
            )
        try:
            issue_ref = validate_github_issue_url(payload.issue_url)
            issue = fetch_github_issue_context(payload.issue_url)
        except (ValueError, GitHubIssueFetchError) as exc:
            _persist_issue_import_failure(
                db,
                payload=payload,
                issue_url=payload.issue_url,
                message=_sanitize_error_message(str(exc)),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_sanitize_error_message(str(exc)),
            ) from exc
        issue_context = issue.model_dump(mode="json")
        issue_url = issue.issue_url
        if repo_url is None and payload.repo_url is None:
            repo_url = issue.repo_url
        if not user_task:
            user_task = _issue_user_task(issue_context)
        if expected_behavior is None:
            expected_behavior = _expected_behavior_from_issue(issue_context)
    else:
        issue_ref = None

    if payload.repo_url:
        settings = get_settings()
        if not settings.github_import_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository import is disabled.",
            )
        try:
            repo_info = validate_github_repo_url(payload.repo_url)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        repo_url = repo_info["repo_url"]

    if not user_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_task is required unless issue_url is provided.",
        )

    run = AgentRun(
        repo_path=repo_path,
        repo_url=repo_url,
        issue_url=issue_url,
        issue_context=_dump_json(issue_context),
        user_task=user_task,
        expected_behavior=expected_behavior,
        test_command=payload.test_command,
        status="created",
        thread_id=str(uuid4()),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    if payload.issue_url and issue_ref is not None:
        log_run_event(
            db,
            run.id,
            "issue_import_started",
            "GitHub issue import started",
            payload={
                "owner": issue_ref["owner"],
                "repo": issue_ref["repo"],
                "issue_number": issue_ref["issue_number"],
                "issue_url": issue_ref["issue_url"],
            },
        )
        log_run_event(
            db,
            run.id,
            "issue_import_completed",
            "GitHub issue import completed",
            payload=_issue_event_payload(issue_context),
        )
    log_run_event(
        db,
        run.id,
        "run_created",
        "Run created",
        payload={
            "status": run.status,
            "repo_path": run.repo_path,
            "repo_url": run.repo_url,
            "issue_url": run.issue_url,
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
    run.fix_strategy = None
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
        repo_path = _effective_repo_path(run, db)
        graph = build_agent_graph()
        _timeout = get_settings().llm_timeout_seconds * 8 or 480
        with _cf.ThreadPoolExecutor(max_workers=1) as _pool:
            _future = _pool.submit(
                graph.invoke,
                {
                    "repo_path": str(repo_path),
                    "user_task": run.user_task,
                    "expected_behavior": run.expected_behavior,
                    "test_command": run.test_command,
                },
                config=_thread_config(run),
            )
            try:
                result = _future.result(timeout=_timeout)
            except _cf.TimeoutError:
                run.status = "failed"
                run.error_message = "Agent run timed out. Try a smaller repository or simpler task."
                db.commit()
                return RunStartResponse(run_id=run.id, status="failed", current_node=None)
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


@router.get("/{run_id}/pr-draft", response_model=PRDraft)
def get_pr_draft(run_id: int, db: Session = Depends(get_db)) -> PRDraft:
    run = _get_run_or_404(run_id, db)
    draft = generate_pr_draft(_pr_draft_state(run))
    log_run_event(
        db,
        run.id,
        "pr_draft_generated",
        "PR draft generated",
        payload={
            "title": draft.title,
            "risk_level": draft.risk_level,
            "verification_status": draft.verification_status,
            "has_issue": draft.linked_issue is not None,
            "files_changed_count": len(draft.files_changed),
        },
    )
    db.commit()
    return draft


@router.post("/{run_id}/approve", response_model=RunStartResponse)
def approve_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    return _resume_run(run_id, "approve", "completed", db)


@router.post("/{run_id}/reject", response_model=RunStartResponse)
def reject_run(run_id: int, db: Session = Depends(get_db)) -> RunStartResponse:
    return _resume_run(run_id, "reject", "rejected", db)


@router.post("/{run_id}/apply-patch", response_model=dict)
def apply_patch(run_id: int, db: Session = Depends(get_db)) -> dict:
    """Apply the stored patch diff to the local repository using the patch command."""
    import subprocess
    import tempfile

    run = _get_run_or_404(run_id, db)

    if not run.patch_diff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No patch diff available for this run.",
        )
    if not run.repo_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patch apply only works for local repository paths.",
        )
    if run.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patch can only be applied after the run has been approved.",
        )

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".patch", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(run.patch_diff)
            tmp_path = tmp.name

        result = subprocess.run(
            ["patch", "-p1", "--dry-run", "-i", tmp_path],
            cwd=run.repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {
                "applied": False,
                "dry_run": True,
                "error": result.stderr or result.stdout or "Patch does not apply cleanly.",
            }

        apply_result = subprocess.run(
            ["patch", "-p1", "-i", tmp_path],
            cwd=run.repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        log_run_event(
            db,
            run.id,
            "patch_applied",
            "Patch applied to repository",
            payload={"returncode": apply_result.returncode, "output": apply_result.stdout[:500]},
        )
        db.commit()

        return {
            "applied": apply_result.returncode == 0,
            "dry_run": False,
            "output": apply_result.stdout or apply_result.stderr or "Patch applied.",
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="`patch` command not found. Install it via your system package manager.",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patch apply timed out.",
        )
    finally:
        import os
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


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


def _effective_repo_path(run: AgentRun, db: Session) -> str:
    if run.repo_path:
        return str(validate_repo_directory(run.repo_path))
    if not run.repo_url:
        raise RuntimeError("Repository path does not exist.")

    repo_info = validate_github_repo_url(run.repo_url)
    log_run_event(
        db,
        run.id,
        "repo_import_started",
        "Repository import started",
        payload={
            "owner": repo_info["owner"],
            "repo": repo_info["repo"],
            "clone_url": repo_info["clone_url"],
        },
    )
    db.commit()

    try:
        imported = import_github_repository(run.repo_url)
    except Exception as exc:
        message = _sanitize_error_message(str(exc)).replace(
            run.repo_url,
            "[repo_url]",
        )
        log_run_event(
            db,
            run.id,
            "repo_import_failed",
            "Repository import failed",
            message=message,
            payload={
                "owner": repo_info["owner"],
                "repo": repo_info["repo"],
                "clone_url": repo_info["clone_url"],
            },
        )
        db.commit()
        raise RuntimeError(message) from exc

    run.repo_path = str(imported.repo_path)
    log_run_event(
        db,
        run.id,
        "repo_import_completed",
        "Repository import completed",
        payload={
            "owner": imported.owner,
            "repo": imported.repo,
            "clone_url": imported.clone_url,
            "workspace_relative_path": imported.workspace_relative_path,
            "used_cache": imported.used_cache,
        },
    )
    db.commit()
    db.refresh(run)
    return run.repo_path


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
    run.fix_strategy = _dump_json(_dict_or_none(result.get("fix_strategy")))
    run.patch_diff = _string_or_none(result.get("patch_diff"))
    run.approval_status = _string_or_none(result.get("approval_status"))
    run.final_report = _string_or_none(result.get("final_report"))
    run.test_result = _dump_json(_dict_or_none(result.get("test_result")))
    run.verification_result = _dump_json(_dict_or_none(result.get("verification_result")))
    run.risk_score = _dump_json(_dict_or_none(result.get("risk_score")))


def _run_read(run: AgentRun) -> RunRead:
    return RunRead(
        id=run.id,
        repo_path=_public_repo_path(run),
        repo_url=run.repo_url,
        issue_url=run.issue_url,
        issue_context=_load_json_dict(run.issue_context),
        user_task=run.user_task,
        expected_behavior=run.expected_behavior,
        test_command=run.test_command,
        status=run.status,
        current_node=run.current_node,
        final_report=run.final_report,
        approval_payload=_load_json_dict(run.approval_payload),
        approval_status=run.approval_status,
        fix_strategy=_load_json_dict(run.fix_strategy),
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
        repo_path=_public_repo_path(run),
        repo_url=run.repo_url,
        issue_url=run.issue_url,
        issue_context=_load_json_dict(run.issue_context),
        final_report=run.final_report,
        approval_status=run.approval_status,
        fix_strategy=_load_json_dict(run.fix_strategy),
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


def _pr_draft_state(run: AgentRun) -> dict[str, object]:
    approval_payload = _load_json_dict(run.approval_payload) or {}
    return {
        "user_task": run.user_task,
        "expected_behavior": run.expected_behavior,
        "issue_context": _load_json_dict(run.issue_context),
        "root_cause": approval_payload.get("root_cause"),
        "fix_strategy": _load_json_dict(run.fix_strategy),
        "patch_diff": run.patch_diff,
        "approval_status": run.approval_status,
        "test_result": _load_json_dict(run.test_result),
        "verification_result": _load_json_dict(run.verification_result),
        "risk_score": _load_json_dict(run.risk_score),
        "final_report": run.final_report,
    }


def _sanitize_error_message(message: str) -> str:
    sanitized = message.strip().splitlines()[0]
    sanitized = ABSOLUTE_PATH_PATTERN.sub("[path]", sanitized)
    sanitized = TOKEN_PATTERN.sub("[token]", sanitized)
    if sanitized.startswith("Repository path does not exist:"):
        return "Repository path does not exist."
    if sanitized.startswith("Repository path is not a directory:"):
        return "Repository path is not a directory."
    if sanitized.startswith("Repository path is outside allowed roots:"):
        return "Repository path is outside allowed roots."
    if sanitized.startswith("GitHub repository import is disabled."):
        return "GitHub repository import is disabled."
    if sanitized.startswith("GitHub issue import is disabled."):
        return "GitHub issue import is disabled."
    return sanitized.replace("Traceback", "").strip() or "Unexpected error."


def _issue_user_task(issue_context: dict[str, object]) -> str:
    title = issue_context.get("title")
    body = issue_context.get("body")
    parts = [str(title).strip()] if isinstance(title, str) and title.strip() else []
    if isinstance(body, str) and body.strip():
        parts.append(body.strip())
    return "\n\n".join(parts)


def _expected_behavior_from_issue(issue_context: dict[str, object]) -> str | None:
    body = issue_context.get("body")
    if not isinstance(body, str):
        return None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(("expected:", "expected behavior:")):
            return stripped
    return None


def _issue_event_payload(issue_context: dict[str, object] | None) -> dict[str, object]:
    if issue_context is None:
        return {}
    return {
        "owner": issue_context.get("owner"),
        "repo": issue_context.get("repo"),
        "issue_number": issue_context.get("issue_number"),
        "issue_url": issue_context.get("issue_url"),
        "labels": issue_context.get("labels"),
        "state": issue_context.get("state"),
    }


def _persist_issue_import_failure(
    db: Session,
    *,
    payload: RunCreate,
    issue_url: str,
    message: str,
) -> None:
    run = AgentRun(
        repo_path=None,
        repo_url=payload.repo_url,
        issue_url=issue_url,
        user_task=payload.user_task.strip() or "GitHub issue import failed.",
        expected_behavior=payload.expected_behavior,
        test_command=payload.test_command,
        status="failed",
        current_node="issue_import",
        error_message=message,
        thread_id=str(uuid4()),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    event_payload: dict[str, object] = {"issue_url": issue_url}
    try:
        issue_ref = validate_github_issue_url(issue_url)
        event_payload.update(
            {
                "owner": issue_ref["owner"],
                "repo": issue_ref["repo"],
                "issue_number": issue_ref["issue_number"],
                "issue_url": issue_ref["issue_url"],
            },
        )
    except ValueError:
        pass
    log_run_event(
        db,
        run.id,
        "issue_import_started",
        "GitHub issue import started",
        payload=event_payload,
    )
    log_run_event(
        db,
        run.id,
        "issue_import_failed",
        "GitHub issue import failed",
        message=message,
        payload=event_payload,
    )
    db.commit()


def _public_repo_path(run: AgentRun) -> str | None:
    if not run.repo_path:
        return None
    if not run.repo_url:
        return run.repo_path

    workspace_root = resolve_path(get_settings().repo_workspace_dir)
    repo_path = resolve_path(run.repo_path)
    try:
        repo_path.relative_to(workspace_root)
    except ValueError:
        return run.repo_path
    return None


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
