from __future__ import annotations

import re
from typing import TypedDict
from urllib.parse import urlparse


SUSPICIOUS_URL_PATTERN = re.compile(r"[\s\\;<>'\"`|]")


class GitHubRepoInfo(TypedDict):
    owner: str
    repo: str
    clone_url: str
    repo_key: str
    repo_url: str


def validate_github_repo_url(value: str) -> GitHubRepoInfo:
    raw = value.strip()
    if not raw:
        raise ValueError("Repository URL is required.")
    if raw.startswith(("file://", "git@", "ssh://")):
        raise ValueError("Only HTTPS GitHub repository URLs are supported.")
    if SUSPICIOUS_URL_PATTERN.search(raw):
        raise ValueError("Repository URL contains unsupported characters.")

    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS GitHub repository URLs are supported.")
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com repository URLs are supported.")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError("Repository URL contains unsupported components.")

    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        raise ValueError("Repository URL must match https://github.com/owner/repo.")

    owner, repo = parts
    if not _valid_segment(owner) or not _valid_segment(repo):
        raise ValueError("Repository URL contains unsupported characters.")

    repo_url = f"https://github.com/{owner}/{repo}"
    return {
        "owner": owner,
        "repo": repo,
        "clone_url": f"{repo_url}.git",
        "repo_key": f"{owner}__{repo}",
        "repo_url": repo_url,
    }


def _valid_segment(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value)) and value not in {".", ".."}
