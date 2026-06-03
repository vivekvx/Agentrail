from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services import github_issues
from app.services.github_issues import fetch_github_issue_context


def test_public_issue_fetch_success_with_mocked_http(monkeypatch: pytest.MonkeyPatch) -> None:
    request_headers: dict[str, str] = {}

    def fake_get(url: str, headers: dict[str, str], timeout_seconds: int) -> dict[str, object]:
        request_headers.update(headers)
        assert url == "https://api.github.com/repos/openai/codex/issues/123"
        assert timeout_seconds == 30
        return {
            "title": "Auth refresh loses token",
            "body": "Expected: user stays signed in.",
            "labels": [{"name": "bug"}, {"name": "auth"}],
            "state": "open",
            "user": {"login": "octocat"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
        }

    monkeypatch.setattr(github_issues, "_github_api_get", fake_get)

    context = fetch_github_issue_context(
        "https://github.com/openai/codex/issues/123",
        settings=Settings(github_token=None),
    )

    assert context.title == "Auth refresh loses token"
    assert context.labels == ["bug", "auth"]
    assert context.author == "octocat"
    assert "Authorization" not in request_headers


def test_404_issue_returns_sanitized_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise github_issues.GitHubIssueFetchError("GitHub issue not found.")

    monkeypatch.setattr(github_issues, "_github_api_get", fake_get)

    with pytest.raises(github_issues.GitHubIssueFetchError, match="not found"):
        fetch_github_issue_context("https://github.com/openai/codex/issues/123")


def test_rate_limit_403_returns_sanitized_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise github_issues.GitHubIssueFetchError("GitHub API rate limit exceeded.")

    monkeypatch.setattr(github_issues, "_github_api_get", fake_get)

    with pytest.raises(github_issues.GitHubIssueFetchError, match="rate limit"):
        fetch_github_issue_context("https://github.com/openai/codex/issues/123")


def test_token_not_leaked_in_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise RuntimeError("failed token ghp_secret_token")

    monkeypatch.setattr(github_issues, "_github_api_get", fake_get)

    with pytest.raises(github_issues.GitHubIssueFetchError) as exc_info:
        fetch_github_issue_context(
            "https://github.com/openai/codex/issues/123",
            settings=Settings(github_token="ghp_secret_token"),
        )

    assert "ghp_secret_token" not in str(exc_info.value)
