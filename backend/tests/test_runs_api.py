from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

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
    assert "Repository path does not exist" in response.json()["detail"]


def test_start_run_failure_sets_failed_status_and_error_message(
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
    assert "Graph execution failed" in start_response.json()["detail"]

    get_response = client.get(f"/api/runs/{run_id}")
    retrieved = get_response.json()
    assert retrieved["status"] == "failed"
    assert retrieved["final_report"] is None
    assert "Repository path does not exist" in retrieved["error_message"]

    with SessionLocal() as db:
        run = db.get(AgentRun, run_id)
        assert run is not None
        assert run.status == "failed"
        assert run.error_message is not None


def test_run_approval_endpoint_returns_interrupt_payload(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(tmp_path / "app.py", "target = 'token persistence'\n")
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Find token persistence",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    approval_response = client.get(f"/api/runs/{run_id}/approval")

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "pending_approval"
    assert approval_response.status_code == 200
    approval = approval_response.json()
    assert approval["status"] == "pending_approval"
    assert approval["approval_payload"]["question"] == "Approve this patch?"
    assert approval["approval_payload"]["root_cause"]


def test_approve_run_resumes_graph_and_saves_final_report(
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

    approve_response = client.post(f"/api/runs/{run_id}/approve")

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == "completed"
    assert approved["has_final_report"] is True
    assert "## Patch Diff" in approved["final_report"]
    assert "## Approval\nPatch approved by user." in approved["final_report"]


def test_reject_run_resumes_graph_and_saves_rejection_report(
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
    assert rejected["has_final_report"] is True
    assert "## Approval\nPatch rejected by user." in rejected["final_report"]
    assert "Reason: Patch rejected by user." in rejected["final_report"]
