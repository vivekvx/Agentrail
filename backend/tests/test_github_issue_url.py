from __future__ import annotations

import pytest

from app.tools.github_issue_url import validate_github_issue_url


def test_valid_issue_url_parses_repo_and_issue_number() -> None:
    result = validate_github_issue_url("https://github.com/openai/codex/issues/123")

    assert result["owner"] == "openai"
    assert result["repo"] == "codex"
    assert result["issue_number"] == 123
    assert result["repo_url"] == "https://github.com/openai/codex"
    assert result["issue_url"] == "https://github.com/openai/codex/issues/123"


def test_issue_url_with_query_and_fragment_is_accepted() -> None:
    result = validate_github_issue_url(
        "https://github.com/openai/codex/issues/123?foo=bar#issuecomment-1",
    )

    assert result["issue_number"] == 123
    assert result["issue_url"] == "https://github.com/openai/codex/issues/123"


def test_pull_request_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="Issue URL must match"):
        validate_github_issue_url("https://github.com/openai/codex/pull/123")


def test_non_github_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="Only github.com"):
        validate_github_issue_url("https://example.com/openai/codex/issues/123")


def test_malformed_issue_number_is_rejected() -> None:
    with pytest.raises(ValueError, match="issue number"):
        validate_github_issue_url("https://github.com/openai/codex/issues/not-a-number")
