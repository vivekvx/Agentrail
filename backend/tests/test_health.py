from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "devpilot-verify",
    }


def test_create_and_get_run(client: TestClient, tmp_path: Path) -> None:
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Investigate failing health check",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0
    assert created["status"] == "created"
    assert created["repo_path"] == str(tmp_path.resolve())
    assert created["user_task"] == "Investigate failing health check"

    get_response = client.get(f"/api/runs/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created


def test_start_run_executes_graph_and_persists_final_report(
    client: TestClient,
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (tmp_path / "requirements.txt").write_text("fastapi\npytest\n", encoding="utf-8")
    (app_dir / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )

    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Find FastAPI app setup",
        },
    )
    created = create_response.json()

    start_response = client.post(f"/api/runs/{created['id']}/start")

    assert start_response.status_code == 200
    started = start_response.json()
    assert started["id"] == created["id"]
    assert started["status"] == "completed"
    assert started["has_final_report"] is True
    assert "# DevPilot Verify Report" in started["final_report"]
    assert "Find FastAPI app setup" in started["final_report"]
    assert "app/main.py:1-2" in started["final_report"]

    get_response = client.get(f"/api/runs/{created['id']}")

    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["status"] == "completed"
    assert retrieved["final_report"] == started["final_report"]


def test_start_run_returns_404_for_missing_run(client: TestClient) -> None:
    response = client.post("/api/runs/999/start")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}
