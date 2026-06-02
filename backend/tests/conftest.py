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


def pytest_sessionfinish() -> None:
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
