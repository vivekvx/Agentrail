from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from app.core.config import get_settings
from app.db.models import Repo
from app.db.session import SessionLocal

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

_GITHUB_RE = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


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
    try:
        repo = db.get(Repo, repo_id)
        if repo is None:
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
            raise RuntimeError(result.stderr.strip()[:500] or "git clone failed")

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
        repo.languages_json = json.dumps(
            [{"name": n, "count": c} for n, c in langs.most_common()]
        )
        repo.tree_json = json.dumps(tree)
        repo.status = "ready"
        repo.error_message = None
        db.commit()
    except subprocess.TimeoutExpired:
        _mark_error(db, repo_id, "Clone timed out")
    except (RepoUrlError, RuntimeError) as exc:
        _mark_error(db, repo_id, str(exc))
    except Exception as exc:  # noqa: BLE001 - surface any failure to the row
        _mark_error(db, repo_id, f"Scan failed: {exc}")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        db.close()


def _mark_error(db, repo_id: int, message: str) -> None:
    repo = db.get(Repo, repo_id)
    if repo is not None:
        repo.status = "error"
        repo.error_message = message
        db.commit()
