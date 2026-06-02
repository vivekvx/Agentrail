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
