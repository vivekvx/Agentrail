from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path


IGNORED_FOLDERS = {
    ".git",
    "node_modules",
    ".venv",
    "dist",
    "build",
    "__pycache__",
}


@dataclass(frozen=True)
class SearchResult:
    file_path: str
    line_number: int
    matched_line: str
    score: int


def search_code(repo_path: str | Path, query: str, max_results: int = 50) -> list[SearchResult]:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")
    if not query:
        raise ValueError("Search query must not be empty")
    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    rg_path = shutil.which("rg")
    if rg_path is not None:
        return _search_with_ripgrep(root, query, max_results, rg_path)
    return _search_with_python(root, query, max_results)


def _search_with_ripgrep(
    root: Path,
    query: str,
    max_results: int,
    rg_path: str,
) -> list[SearchResult]:
    command = [
        rg_path,
        "--fixed-strings",
        "--line-number",
        "--no-heading",
        "--color",
        "never",
    ]
    for folder in sorted(IGNORED_FOLDERS):
        command.extend(["--glob", f"!{folder}/**"])
    command.extend([query, "."])

    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(f"ripgrep search failed: {completed.stderr.strip()}")

    results: list[SearchResult] = []
    for output_line in completed.stdout.splitlines():
        parsed = _parse_ripgrep_line(output_line, query)
        if parsed is None:
            continue
        results.append(parsed)
        if len(results) >= max_results:
            break
    return results


def _parse_ripgrep_line(output_line: str, query: str) -> SearchResult | None:
    parts = output_line.split(":", 2)
    if len(parts) != 3:
        return None
    file_path, line_number_text, matched_line = parts
    try:
        line_number = int(line_number_text)
    except ValueError:
        return None
    return SearchResult(
        file_path=_normalize_relative_path(file_path),
        line_number=line_number,
        matched_line=matched_line.strip(),
        score=_score_line(matched_line, query),
    )


def _search_with_python(root: Path, query: str, max_results: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    query_lower = query.lower()
    for file_path in _iter_searchable_files(root):
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        relative_path = file_path.relative_to(root).as_posix()
        for line_number, line in enumerate(lines, start=1):
            if query_lower not in line.lower():
                continue
            results.append(
                SearchResult(
                    file_path=relative_path,
                    line_number=line_number,
                    matched_line=line.strip(),
                    score=_score_line(line, query),
                ),
            )
            if len(results) >= max_results:
                return results
    return results


def _iter_searchable_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_FOLDERS for part in relative_parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda file_path: file_path.relative_to(root).as_posix())


def _score_line(line: str, query: str) -> int:
    score = line.lower().count(query.lower())
    return max(score, 1)


def _normalize_relative_path(file_path: str) -> str:
    normalized = file_path.removeprefix("./")
    return Path(normalized).as_posix()
