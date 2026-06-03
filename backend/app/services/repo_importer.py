from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.tools.github_url import GitHubRepoInfo, validate_github_repo_url
from app.tools.path_policy import resolve_path


@dataclass(frozen=True)
class RepoImportResult:
    repo_path: Path
    owner: str
    repo: str
    clone_url: str
    repo_url: str
    repo_key: str
    workspace_relative_path: str
    used_cache: bool


def import_github_repository(
    repo_url: str,
    *,
    settings: Settings | None = None,
) -> RepoImportResult:
    active_settings = settings or get_settings()
    if not active_settings.github_import_enabled:
        raise RuntimeError("GitHub repository import is disabled.")

    repo_info = validate_github_repo_url(repo_url)
    workspace_root = _workspace_root(active_settings)
    workspace_root.mkdir(parents=True, exist_ok=True)
    destination = resolve_path(workspace_root / repo_info["repo_key"])
    _ensure_within_workspace(destination, workspace_root)

    if destination.exists():
        if not destination.is_dir() or not (destination / ".git").exists():
            raise RuntimeError("Cached repository path is invalid.")
        _ensure_repo_size(destination, active_settings.max_repo_size_mb)
        return _result(repo_info, destination, used_cache=True)

    command = [
        "git",
        "clone",
        "--depth=1",
        repo_info["clone_url"],
        str(destination),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=active_settings.git_clone_timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        _cleanup_partial_clone(destination)
        raise RuntimeError("Git clone timed out.") from exc
    except OSError as exc:
        _cleanup_partial_clone(destination)
        raise RuntimeError("Git is unavailable.") from exc

    if completed.returncode != 0:
        _cleanup_partial_clone(destination)
        raise RuntimeError(_sanitize_git_error(completed.stderr or completed.stdout))

    _ensure_repo_size(destination, active_settings.max_repo_size_mb)
    return _result(repo_info, destination, used_cache=False)


def _workspace_root(settings: Settings) -> Path:
    return resolve_path(settings.repo_workspace_dir)


def _ensure_within_workspace(path: Path, workspace_root: Path) -> None:
    try:
        path.relative_to(workspace_root)
    except ValueError as exc:
        raise RuntimeError("Repository workspace path is invalid.") from exc


def _ensure_repo_size(repo_path: Path, max_repo_size_mb: int) -> None:
    max_bytes = max_repo_size_mb * 1024 * 1024
    total_bytes = 0
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        total_bytes += file_path.stat().st_size
        if total_bytes > max_bytes:
            raise RuntimeError("Imported repository exceeds size limit.")


def _cleanup_partial_clone(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _sanitize_git_error(message: str) -> str:
    first_line = message.strip().splitlines()[0] if message.strip() else ""
    lowered = first_line.lower()
    if "repository not found" in lowered:
        return "Git clone failed: repository not found."
    if "could not read username" in lowered or "authentication failed" in lowered:
        return "Git clone failed: authentication failed."
    if not first_line:
        return "Git clone failed."
    return f"Git clone failed: {first_line}"


def _result(
    repo_info: GitHubRepoInfo,
    destination: Path,
    *,
    used_cache: bool,
) -> RepoImportResult:
    return RepoImportResult(
        repo_path=destination,
        owner=repo_info["owner"],
        repo=repo_info["repo"],
        clone_url=repo_info["clone_url"],
        repo_url=repo_info["repo_url"],
        repo_key=repo_info["repo_key"],
        workspace_relative_path=repo_info["repo_key"],
        used_cache=used_cache,
    )
