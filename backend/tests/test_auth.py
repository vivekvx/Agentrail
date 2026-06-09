from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "user@example.com", password: str = "pass123") -> str:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_token(client: TestClient) -> None:
    res = client.post("/api/auth/register", json={"email": "a@b.com", "password": "secret"})
    assert res.status_code == 201
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"


def test_register_duplicate_email_409(client: TestClient) -> None:
    _register(client)
    res = client.post("/api/auth/register", json={"email": "user@example.com", "password": "other"})
    assert res.status_code == 409


def test_login_valid_credentials(client: TestClient) -> None:
    _register(client)
    res = client.post("/api/auth/login", json={"email": "user@example.com", "password": "pass123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password_401(client: TestClient) -> None:
    _register(client)
    res = client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_email_401(client: TestClient) -> None:
    res = client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "pw"})
    assert res.status_code == 401


def test_authenticated_user_sees_only_own_runs(client: TestClient, tmp_path) -> None:
    token_a = _register(client, "a@test.com", "pw")
    token_b = _register(client, "b@test.com", "pw")

    client.post(
        "/api/runs",
        json={"repo_path": str(tmp_path), "user_task": "fix bug"},
        headers=_auth_headers(token_a),
    )

    runs_a = client.get("/api/runs", headers=_auth_headers(token_a)).json()
    assert len(runs_a) == 1

    runs_b = client.get("/api/runs", headers=_auth_headers(token_b)).json()
    assert len(runs_b) == 0


def test_unauthenticated_list_returns_all_runs(client: TestClient, tmp_path) -> None:
    token = _register(client)
    client.post(
        "/api/runs",
        json={"repo_path": str(tmp_path), "user_task": "fix bug"},
        headers=_auth_headers(token),
    )
    res = client.get("/api/runs")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_invalid_token_treated_as_unauthenticated(client: TestClient) -> None:
    res = client.get("/api/runs", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 200
