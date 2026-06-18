from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.api.routes_repos as routes_repos
from app.services.repo_scanner import RepoUrlError, _build_tree, parse_github_url


# ── parse_github_url (pure) ────────────────────────────────────────────


def test_parse_github_url_normalizes_clone_url_and_name() -> None:
    clone_url, name = parse_github_url("https://github.com/pallets/flask")
    assert clone_url == "https://github.com/pallets/flask.git"
    assert name == "pallets/flask"


def test_parse_github_url_strips_dot_git_and_trailing_slash() -> None:
    _, name = parse_github_url("https://github.com/pallets/flask.git/")
    assert name == "pallets/flask"


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/foo/bar",
        "http://github.com/foo/bar",  # not https
        "https://github.com/onlyowner",
        "ftp://github.com/foo/bar",
        "not a url",
        "",
    ],
)
def test_parse_github_url_rejects_non_github(url: str) -> None:
    with pytest.raises(RepoUrlError):
        parse_github_url(url)


# ── _build_tree (pure, file system) ────────────────────────────────────


def test_build_tree_counts_files_detects_langs_and_skips_ignored(tmp_path: Path) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("x = 1\n")
    (tmp_path / "app" / "util.py").write_text("y = 2\n")
    (tmp_path / "index.ts").write_text("export {}\n")
    # Ignored dir must not be walked.
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("module.exports={}\n")

    tree, file_count, langs = _build_tree(tmp_path, max_files=1000)

    assert file_count == 3  # node_modules excluded
    assert langs["Python"] == 2
    assert langs["TypeScript"] == 1
    assert "JavaScript" not in langs
    top_level = {c["name"] for c in tree["children"]}
    assert "node_modules" not in top_level
    assert "app" in top_level


def test_build_tree_respects_max_files_cap(tmp_path: Path) -> None:
    for i in range(10):
        (tmp_path / f"f{i}.py").write_text("x\n")
    _, file_count, _ = _build_tree(tmp_path, max_files=5)
    assert file_count == 5


# ── import endpoint guards ─────────────────────────────────────────────


@pytest.fixture()
def no_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop the background clone from running during endpoint tests."""
    monkeypatch.setattr(routes_repos, "scan_repo", lambda repo_id: None)


def test_import_valid_repo_returns_201_pending(
    client: TestClient, no_scan: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(routes_repos, "fetch_repo_size_kb", lambda name: 1234)
    res = client.post("/api/repos", json={"url": "https://github.com/pallets/flask"})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["name"] == "pallets/flask"
    assert body["status"] == "pending"


def test_import_non_github_url_returns_422(client: TestClient, no_scan: None) -> None:
    res = client.post("/api/repos", json={"url": "https://gitlab.com/foo/bar"})
    assert res.status_code == 422


def test_import_missing_repo_returns_422(
    client: TestClient, no_scan: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _missing(name: str) -> int:
        raise RepoUrlError("Repository not found or not public")

    monkeypatch.setattr(routes_repos, "fetch_repo_size_kb", _missing)
    res = client.post("/api/repos", json={"url": "https://github.com/nope/nope"})
    assert res.status_code == 422
    assert "not found" in res.json()["detail"].lower()


def test_import_oversized_repo_returns_413(
    client: TestClient, no_scan: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1 GB in KB, well over the default 200 MB cap.
    monkeypatch.setattr(routes_repos, "fetch_repo_size_kb", lambda name: 1_000_000)
    res = client.post("/api/repos", json={"url": "https://github.com/big/repo"})
    assert res.status_code == 413


def test_get_unknown_repo_returns_404(client: TestClient) -> None:
    res = client.get("/api/repos/9999")
    assert res.status_code == 404


def test_import_then_get_roundtrips_summary_fields(
    client: TestClient, no_scan: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(routes_repos, "fetch_repo_size_kb", lambda name: 10)
    created = client.post(
        "/api/repos", json={"url": "https://github.com/octocat/Hello-World"}
    ).json()
    fetched = client.get(f"/api/repos/{created['id']}").json()
    assert fetched["id"] == created["id"]
    assert fetched["name"] == "octocat/Hello-World"
    assert fetched["languages"] == []
