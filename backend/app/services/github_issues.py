from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.tools.github_issue_url import validate_github_issue_url


class GitHubIssueFetchError(RuntimeError):
    pass


class GitHubIssueContext(BaseModel):
    owner: str
    repo: str
    issue_number: int
    issue_url: str
    repo_url: str
    title: str
    body: str | None
    labels: list[str]
    state: str
    author: str | None
    created_at: str | None
    updated_at: str | None


def fetch_github_issue_context(
    issue_url: str,
    *,
    settings: Settings | None = None,
) -> GitHubIssueContext:
    settings = settings or get_settings()
    ref = validate_github_issue_url(issue_url)
    api_url = (
        f"https://api.github.com/repos/{ref['owner']}/{ref['repo']}"
        f"/issues/{ref['issue_number']}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Agentrail",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        payload = _github_api_get(
            api_url,
            headers=headers,
            timeout_seconds=settings.github_api_timeout_seconds,
        )
    except GitHubIssueFetchError:
        raise
    except Exception as exc:
        raise GitHubIssueFetchError(_sanitize_error(str(exc), settings)) from exc

    if "pull_request" in payload:
        raise GitHubIssueFetchError("GitHub pull request URLs are not supported for issue import.")

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise GitHubIssueFetchError("GitHub issue response did not include a title.")

    labels = _labels(payload.get("labels"))
    user = payload.get("user")
    author = user.get("login") if isinstance(user, dict) and isinstance(user.get("login"), str) else None
    body = payload.get("body")
    if isinstance(body, str):
        body = body[: settings.max_issue_body_chars]
    else:
        body = None

    return GitHubIssueContext(
        owner=ref["owner"],
        repo=ref["repo"],
        issue_number=ref["issue_number"],
        issue_url=ref["issue_url"],
        repo_url=ref["repo_url"],
        title=title.strip(),
        body=body,
        labels=labels,
        state=_string_or_default(payload.get("state"), "unknown"),
        author=author,
        created_at=_string_or_none(payload.get("created_at")),
        updated_at=_string_or_none(payload.get("updated_at")),
    )


def _github_api_get(
    url: str,
    *,
    headers: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise GitHubIssueFetchError(_http_error_message(exc)) from exc
    except urllib.error.URLError as exc:
        raise GitHubIssueFetchError("GitHub issue import failed.") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GitHubIssueFetchError("GitHub issue response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise GitHubIssueFetchError("GitHub issue response was not an object.")
    return payload


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    if exc.code == 404:
        return "GitHub issue not found."
    if exc.code == 403:
        return "GitHub issue import was forbidden or rate limited."
    return f"GitHub issue import failed with status {exc.code}."


def _labels(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    labels: list[str] = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            labels.append(item["name"])
        elif isinstance(item, str):
            labels.append(item)
    return labels


def _sanitize_error(message: str, settings: Settings) -> str:
    sanitized = message.strip().splitlines()[0]
    if settings.github_token:
        sanitized = sanitized.replace(settings.github_token, "[token]")
    sanitized = sanitized.replace("Traceback", "").strip()
    return sanitized or "GitHub issue import failed."


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _string_or_default(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default
