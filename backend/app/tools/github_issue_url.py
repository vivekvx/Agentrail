from __future__ import annotations

import re
from typing import TypedDict
from urllib.parse import urlparse


SUSPICIOUS_URL_PATTERN = re.compile(r"[\s\\;<>'\"`|]")


class GitHubIssueRef(TypedDict):
    owner: str
    repo: str
    issue_number: int
    repo_url: str
    issue_url: str


def validate_github_issue_url(value: str) -> GitHubIssueRef:
    raw = value.strip()
    if not raw:
        raise ValueError("Issue URL is required.")
    if raw.startswith(("file://", "git@", "ssh://")):
        raise ValueError("Only HTTPS GitHub issue URLs are supported.")
    if SUSPICIOUS_URL_PATTERN.search(raw):
        raise ValueError("Issue URL contains unsupported characters.")

    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS GitHub issue URLs are supported.")
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com issue URLs are supported.")
    if parsed.params:
        raise ValueError("Issue URL contains unsupported components.")

    parts = [part for part in parsed.path.rstrip("/").split("/") if part]
    if len(parts) != 4 or parts[2] != "issues":
        raise ValueError("Issue URL must match https://github.com/owner/repo/issues/123.")

    owner, repo, _, number_text = parts
    if not _valid_segment(owner) or not _valid_segment(repo):
        raise ValueError("Issue URL contains unsupported characters.")
    if not number_text.isdigit() or int(number_text) <= 0:
        raise ValueError("Issue URL issue number must be a positive integer.")

    issue_number = int(number_text)
    repo_url = f"https://github.com/{owner}/{repo}"
    issue_url = f"{repo_url}/issues/{issue_number}"
    return {
        "owner": owner,
        "repo": repo,
        "issue_number": issue_number,
        "repo_url": repo_url,
        "issue_url": issue_url,
    }


def _valid_segment(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value)) and value not in {".", ".."}
