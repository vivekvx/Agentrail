from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable


ALLOWED_ROOTS_ENV = "AGENTRAIL_ALLOWED_REPO_ROOTS"
LEGACY_ALLOWED_ROOTS_ENV = "DEVPILOT_ALLOWED_REPO_ROOTS"
SECRET_FILE_PATTERNS = (
    ".env",
    ".env.",
    "secrets.",
    ".pem",
    ".key",
)


def validate_repo_directory(
    repo_path: str | Path,
    *,
    allowed_roots: Iterable[str | Path] | None = None,
) -> Path:
    resolved_path = resolve_path(repo_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {resolved_path}")
    if not resolved_path.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {resolved_path}")
    if not is_path_allowed(resolved_path, allowed_roots=allowed_roots):
        raise PermissionError(f"Repository path is outside allowed roots: {resolved_path}")
    return resolved_path


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def is_path_allowed(
    path: str | Path,
    *,
    allowed_roots: Iterable[str | Path] | None = None,
) -> bool:
    resolved_path = resolve_path(path)
    roots = _allowed_roots(allowed_roots)
    return any(_is_relative_to(resolved_path, root) for root in roots)


def is_excluded_secret_file(path: str | Path) -> bool:
    name = Path(path).name.lower()
    if name == ".env" or name.startswith(".env."):
        return True
    if name.startswith("secrets."):
        return True
    return any(
        name.endswith(pattern)
        for pattern in SECRET_FILE_PATTERNS
        if pattern.startswith(".") and pattern not in {".env", ".env."}
    )


def _allowed_roots(allowed_roots: Iterable[str | Path] | None) -> list[Path]:
    if allowed_roots is not None:
        roots = list(allowed_roots)
    else:
        configured_roots = os.getenv(ALLOWED_ROOTS_ENV) or os.getenv(LEGACY_ALLOWED_ROOTS_ENV)
        if configured_roots:
            roots = [root for root in configured_roots.split(os.pathsep) if root]
        else:
            roots = [Path.home(), Path(tempfile.gettempdir())]
    return [resolve_path(root) for root in roots]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
