from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from app.core.config import get_settings
from app.db.models import Repo
from app.db.session import SessionLocal

logger = logging.getLogger("agentrail.repo_scanner")

# Bound concurrent clones so a burst of imports cannot exhaust CPU/disk.
_scan_semaphore = threading.BoundedSemaphore(get_settings().max_concurrent_scans)

# Map file extensions to language labels for stack detection.
_EXT_LANG = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".css": "CSS",
    ".scss": "CSS",
    ".html": "HTML",
    ".md": "Markdown",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
}

_IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".turbo",
    ".cache",
    "target",
    ".idea",
    ".vscode",
}

_GITHUB_RE = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


class RepoUrlError(ValueError):
    """Raised when a repository URL is not an importable public GitHub URL."""


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (normalized_clone_url, name) or raise RepoUrlError."""
    url = (url or "").strip()
    match = _GITHUB_RE.match(url)
    if not match:
        raise RepoUrlError("Only public https://github.com/<owner>/<repo> URLs are supported")
    owner, repo = match.group(1), match.group(2)
    return f"https://github.com/{owner}/{repo}.git", f"{owner}/{repo}"


def fetch_repo_size_kb(name: str) -> int:
    """Look up a repo's size (KB) via the GitHub API.

    Existence + size pre-check so oversized or missing repos are rejected
    before any clone runs. Raises RepoUrlError on 404 / unexpected response.
    """
    settings = get_settings()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{name}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "agentrail"},
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.github_api_timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RepoUrlError("Repository not found or not public")
        if exc.code == 403:
            raise RepoUrlError("GitHub API rate limit reached; try again later")
        raise RepoUrlError(f"GitHub API error ({exc.code})")
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise RepoUrlError("Could not reach GitHub to verify the repository")

    size = data.get("size")
    if not isinstance(size, int):
        raise RepoUrlError("Unexpected GitHub API response")
    return size


def _workspace_for(repo_id: int) -> Path:
    settings = get_settings()
    root = Path(settings.repo_workspace_dir).resolve()
    return root / str(repo_id)


def _build_tree(root: Path, max_files: int) -> tuple[dict, int, Counter]:
    """Walk the repo into a nested tree dict. Returns (tree, file_count, langs)."""
    file_count = 0
    langs: Counter[str] = Counter()
    tree: dict = {"name": root.name, "type": "dir", "children": []}
    nodes = {root: tree}

    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORE_DIRS)
        cur_path = Path(current)
        parent = nodes.get(cur_path)
        if parent is None:
            continue
        for d in dirs:
            child = {"name": d, "type": "dir", "children": []}
            parent["children"].append(child)
            nodes[cur_path / d] = child
        for f in sorted(files):
            if file_count >= max_files:
                break
            ext = Path(f).suffix.lower()
            lang = _EXT_LANG.get(ext)
            if lang:
                langs[lang] += 1
            parent["children"].append({"name": f, "type": "file", "lang": lang})
            file_count += 1

    return tree, file_count, langs


def scan_repo(repo_id: int) -> None:
    """Clone (shallow) and scan a repo. Runs in a background thread.

    Updates the Repo row status through scanning -> ready/error. Safe to call
    detached: opens its own DB session and cleans up the workspace.
    """
    db = SessionLocal()
    workspace = _workspace_for(repo_id)
    acquired = False
    try:
        repo = db.get(Repo, repo_id)
        if repo is None:
            return

        settings = get_settings()
        acquired = _scan_semaphore.acquire(timeout=settings.git_clone_timeout_seconds)
        if not acquired:
            _mark_error(db, repo_id, "Server busy; please retry shortly")
            return

        repo.status = "scanning"
        db.commit()

        clone_url, _ = parse_github_url(repo.url)
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
        workspace.parent.mkdir(parents=True, exist_ok=True)

        settings = get_settings()
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(workspace)],
            capture_output=True,
            text=True,
            timeout=settings.git_clone_timeout_seconds,
        )
        if result.returncode != 0:
            # Log full stderr server-side; never surface it to the client
            # (it can leak local paths / internal detail).
            logger.warning("git clone failed for repo %s: %s", repo_id, result.stderr.strip())
            raise RuntimeError("Could not clone the repository")

        branch = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        default_branch = branch.stdout.strip() or None

        tree, file_count, langs = _build_tree(workspace, settings.max_repo_files)
        tree["name"] = repo.name.split("/")[-1]

        repo.default_branch = default_branch
        repo.file_count = file_count
        repo.languages_json = json.dumps([{"name": n, "count": c} for n, c in langs.most_common()])
        repo.tree_json = json.dumps(tree)

        # Best-effort: build the chat index while the clone is still on disk.
        # If Ollama is down the repo is still usable for map/tree/tour.
        try:
            from app.services import rag

            repo.chunks_json = json.dumps(rag.build_index(workspace))
        except Exception as exc:  # noqa: BLE001 - chat is optional
            logger.warning("chat index skipped for repo %s: %s", repo_id, exc)

        repo.status = "ready"
        repo.error_message = None
        db.commit()
    except subprocess.TimeoutExpired:
        _mark_error(db, repo_id, "Clone timed out")
    except (RepoUrlError, RuntimeError) as exc:
        _mark_error(db, repo_id, str(exc))
    except Exception:  # noqa: BLE001 - record a generic failure, log the detail
        logger.exception("scan failed for repo %s", repo_id)
        _mark_error(db, repo_id, "Scan failed")
    finally:
        if acquired:
            _scan_semaphore.release()
        shutil.rmtree(workspace, ignore_errors=True)
        db.close()


def _mark_error(db, repo_id: int, message: str) -> None:
    repo = db.get(Repo, repo_id)
    if repo is not None:
        repo.status = "error"
        repo.error_message = message
        db.commit()
