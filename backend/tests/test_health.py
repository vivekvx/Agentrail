from __future__ import annotations

import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_devpilot_verify.db"

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app


DB_PATH = Path("test_devpilot_verify.db")


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def teardown_module() -> None:
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "devpilot-verify",
    }


def test_create_and_get_run(client: TestClient) -> None:
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": "/tmp/example-fastapi-app",
            "user_task": "Investigate failing health check",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0
    assert created["status"] == "created"
    assert created["repo_path"] == "/tmp/example-fastapi-app"
    assert created["user_task"] == "Investigate failing health check"

    get_response = client.get(f"/api/runs/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created
