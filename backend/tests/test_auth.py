from __future__ import annotations

from fastapi.testclient import TestClient


def _register(
    client: TestClient, email: str = "user@example.com", password: str = "pass123"
) -> str:
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
