from __future__ import annotations

import pytest

from app.tools.github_url import validate_github_repo_url


def test_validate_github_url_normalizes_public_repo() -> None:
    result = validate_github_repo_url("https://github.com/fastapi/fastapi")

    assert result == {
        "owner": "fastapi",
        "repo": "fastapi",
        "clone_url": "https://github.com/fastapi/fastapi.git",
        "repo_key": "fastapi__fastapi",
        "repo_url": "https://github.com/fastapi/fastapi",
    }


def test_validate_github_url_normalizes_dot_git_repo() -> None:
    result = validate_github_repo_url("https://github.com/fastapi/fastapi.git")

    assert result["clone_url"] == "https://github.com/fastapi/fastapi.git"
    assert result["repo_url"] == "https://github.com/fastapi/fastapi"


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/fastapi/fastapi",
        "file:///tmp/repo",
        "git@github.com:fastapi/fastapi.git",
        "ssh://github.com/fastapi/fastapi.git",
        "https://github.com/fastapi/fastapi;rm -rf /",
    ],
)
def test_validate_github_url_rejects_unsupported_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_github_repo_url(url)
