from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAX_FILE_SIZE_BYTES = 256_000
SECRET_NAME_PARTS = {
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "api_key",
    "apikey",
    "token",
}


@dataclass(frozen=True)
class FileSnippet:
    file_path: str
    start_line: int
    end_line: int
    lines: list[str]


def read_text_file(
    repo_root: str | Path,
    file_path: str | Path,
    *,
    start_line: int = 1,
    end_line: int | None = None,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> FileSnippet:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository root is not a directory: {root}")
    if start_line < 1:
        raise ValueError("start_line must be at least 1")
    if end_line is not None and end_line < start_line:
        raise ValueError("end_line must be greater than or equal to start_line")
    if max_file_size_bytes < 1:
        raise ValueError("max_file_size_bytes must be at least 1")

    requested_path = Path(file_path).expanduser()
    target = requested_path if requested_path.is_absolute() else root / requested_path
    target = target.resolve()
    if not _is_relative_to(target, root):
        raise PermissionError(f"Cannot read file outside repo root: {target}")
    if not target.exists():
        raise FileNotFoundError(f"File does not exist: {target}")
    if not target.is_file():
        raise IsADirectoryError(f"Path is not a file: {target}")
    if _looks_secret(target):
        raise PermissionError(f"Refusing to read secret-looking file: {target.name}")

    file_size = target.stat().st_size
    if file_size > max_file_size_bytes:
        raise ValueError(
            f"File exceeds max file size: {file_size} > {max_file_size_bytes} bytes",
        )

    lines = _read_lines(target)
    total_lines = len(lines)
    final_end_line = end_line if end_line is not None else total_lines
    selected_lines = lines[start_line - 1 : final_end_line]

    return FileSnippet(
        file_path=target.relative_to(root).as_posix(),
        start_line=start_line,
        end_line=start_line + len(selected_lines) - 1 if selected_lines else start_line - 1,
        lines=[
            f"{line_number}: {line}"
            for line_number, line in enumerate(selected_lines, start=start_line)
        ],
    )


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"File is not valid UTF-8 text: {path}") from exc


def _looks_secret(path: Path) -> bool:
    lower_parts = [part.lower() for part in path.parts]
    name = path.name.lower()
    stem = path.stem.lower()

    if name == ".env" or name.startswith(".env."):
        return True
    for part in lower_parts:
        if part == ".env" or part.startswith(".env."):
            return True
    for marker in SECRET_NAME_PARTS:
        if marker in name or marker in stem:
            return True
    return False


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
