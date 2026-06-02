from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import routes_runs
from app.db.models import AgentRun
from app.db.session import SessionLocal


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_create_run_rejects_invalid_repo_path(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path / "missing"),
            "user_task": "Find FastAPI app setup",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository path does not exist."


def test_create_run_returns_initial_fields(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix auth refresh bug",
            "expected_behavior": "Token should persist across refresh.",
            "test_command": "python -m pytest",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["repo_path"] == str(tmp_path.resolve())
    assert created["user_task"] == "Fix auth refresh bug"
    assert created["expected_behavior"] == "Token should persist across refresh."
    assert created["test_command"] == "python -m pytest"
    assert created["status"] == "created"
    assert created["current_node"] is None
    assert created["approval_payload"] is None
    assert created["approval_status"] is None
    assert created["patch_diff"] is None
    assert created["test_result"] is None
    assert created["verification_result"] is None
    assert created["risk_score"] is None
    assert created["final_report"] is None
    assert created["error_message"] is None

    events_response = client.get(f"/api/runs/{created['id']}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert [event["event_type"] for event in events] == ["run_created"]
    assert events[0]["payload"]["status"] == "created"


def test_start_run_failure_sets_failed_status_and_sanitized_error_message(
    client: TestClient,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(repo),
            "user_task": "Find FastAPI app setup",
        },
    )
    run_id = create_response.json()["id"]
    repo.rmdir()

    start_response = client.post(f"/api/runs/{run_id}/start")

    assert start_response.status_code == 500
    assert start_response.json()["detail"] == "Graph execution failed."

    get_response = client.get(f"/api/runs/{run_id}")
    retrieved = get_response.json()
    assert retrieved["status"] == "failed"
    assert retrieved["final_report"] is None
    assert retrieved["error_message"] == "Repository path does not exist."
    assert str(repo.resolve()) not in retrieved["error_message"]

    with SessionLocal() as db:
        run = db.get(AgentRun, run_id)
        assert run is not None
        assert run.status == "failed"
        assert run.error_message is not None


def test_start_run_persists_pending_approval_patch_diff_and_payload(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    get_response = client.get(f"/api/runs/{run_id}")

    assert start_response.status_code == 200
    started = start_response.json()
    assert started["status"] == "pending_approval"
    assert started["current_node"] == "approval_node"
    assert started["approval_payload"]["question"] == "Approve this patch?"
    assert "AuthContext.tsx" in started["patch_diff"]

    assert get_response.status_code == 200
    run = get_response.json()
    assert run["status"] == "pending_approval"
    assert run["approval_payload"]["question"] == "Approve this patch?"
    assert run["approval_payload"]["root_cause"]
    assert "AuthContext.tsx" in run["patch_diff"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "run_started" in event_types
    assert "pending_approval" in event_types


def test_get_run_returns_patch_diff_and_approval_payload(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    created = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    ).json()

    client.post(f"/api/runs/{created['id']}/start")
    response = client.get(f"/api/runs/{created['id']}")

    assert response.status_code == 200
    run = response.json()
    assert run["approval_payload"]["question"] == "Approve this patch?"
    assert "diff --git" in run["patch_diff"]

    events_response = client.get(f"/api/runs/{created['id']}/events")
    events = events_response.json()
    assert events[0]["event_type"] == "run_created"
    assert events[1]["event_type"] == "run_started"
    assert any(event["event_type"] == "pending_approval" for event in events)


def test_approve_run_persists_final_report_test_result_verification_and_risk(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    write_file(tmp_path / "test_sample.py", "def test_sample():\n    assert True\n")
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
            "test_command": "python -m pytest",
        },
    )
    run_id = create_response.json()["id"]
    client.post(f"/api/runs/{run_id}/start")

    approve_response = client.post(f"/api/runs/{run_id}/approve")

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == "completed"
    assert approved["approval_status"] == "approved"
    assert approved["current_node"] == "reporter"
    assert approved["has_final_report"] is True
    assert approved["test_result"]["status"] == "passed"
    assert approved["verification_result"]["status"] == "verified"
    assert approved["risk_score"]["level"] in {"medium", "high"}
    assert "## Patch Diff" in approved["final_report"]
    assert "## Verification" in approved["final_report"]
    assert "## Risk Score" in approved["final_report"]

    get_response = client.get(f"/api/runs/{run_id}")
    persisted = get_response.json()
    assert persisted["final_report"] == approved["final_report"]
    assert persisted["test_result"]["status"] == "passed"
    assert persisted["verification_result"]["status"] == "verified"
    assert persisted["risk_score"]["level"] in {"medium", "high"}

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "approved" in event_types
    assert "tests_run" in event_types
    assert "verified" in event_types
    assert "risk_scored" in event_types
    assert "report_generated" in event_types
    assert "run_completed" in event_types


def test_reject_run_persists_final_report_and_approval_status(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    )
    run_id = create_response.json()["id"]
    client.post(f"/api/runs/{run_id}/start")

    reject_response = client.post(f"/api/runs/{run_id}/reject")

    assert reject_response.status_code == 200
    rejected = reject_response.json()
    assert rejected["status"] == "rejected"
    assert rejected["approval_status"] == "rejected"
    assert rejected["has_final_report"] is True
    assert rejected["verification_result"]["status"] == "rejected"
    assert rejected["risk_score"]["level"] == "high"
    assert "## Approval\nPatch rejected by user." in rejected["final_report"]
    assert "Reason: Patch rejected by user." in rejected["final_report"]

    get_response = client.get(f"/api/runs/{run_id}")
    persisted = get_response.json()
    assert persisted["approval_status"] == "rejected"
    assert persisted["final_report"] == rejected["final_report"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "rejected" in event_types
    assert "report_generated" in event_types


def test_get_run_does_not_expose_raw_tracebacks(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenGraph:
        def invoke(self, *_args: object, **_kwargs: object) -> dict[str, object]:
            raise RuntimeError(
                f"Traceback: failure while reading {tmp_path / 'secret.py'}\nextra traceback line",
            )

    monkeypatch.setattr(routes_runs, "build_agent_graph", lambda: BrokenGraph())

    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Cause graph failure",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    assert start_response.status_code == 500
    assert start_response.json()["detail"] == "Graph execution failed."

    get_response = client.get(f"/api/runs/{run_id}")
    run = get_response.json()
    assert run["status"] == "failed"
    assert "Traceback" not in run["error_message"]
    assert str(tmp_path.resolve()) not in run["error_message"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "run_failed" in event_types
