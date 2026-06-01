from __future__ import annotations

from pathlib import Path

import pytest

from app.tools import search_tools
from app.tools.search_tools import SearchResult, search_code


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_search_code_falls_back_to_python_and_skips_ignored_folders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(search_tools.shutil, "which", lambda _: None)
    write_file(tmp_path / "app" / "main.py", "needle = 'one'\nprint(needle)\n")
    write_file(tmp_path / "node_modules" / "pkg" / "index.js", "needle\n")
    write_file(tmp_path / ".git" / "config", "needle\n")
    write_file(tmp_path / "dist" / "bundle.js", "needle\n")
    write_file(tmp_path / "build" / "output.txt", "needle\n")
    write_file(tmp_path / ".venv" / "lib.py", "needle\n")
    write_file(tmp_path / "__pycache__" / "cache.pyc", "needle\n")

    results = search_code(tmp_path, "needle", max_results=10)

    assert results == [
        SearchResult(
            file_path="app/main.py",
            line_number=1,
            matched_line="needle = 'one'",
            score=1,
        ),
        SearchResult(
            file_path="app/main.py",
            line_number=2,
            matched_line="print(needle)",
            score=1,
        ),
    ]


def test_search_code_limits_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search_tools.shutil, "which", lambda _: None)
    write_file(tmp_path / "app.py", "target\nnope\ntarget\ntarget\n")

    results = search_code(tmp_path, "target", max_results=2)

    assert [result.line_number for result in results] == [1, 3]


def test_search_code_uses_ripgrep_when_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = [
        SearchResult(
            file_path="src/app.py",
            line_number=7,
            matched_line="target_call()",
            score=1,
        ),
    ]
    calls: list[tuple[Path, str, int, str]] = []

    def fake_rg(
        root: Path,
        query: str,
        max_results: int,
        rg_path: str,
    ) -> list[SearchResult]:
        calls.append((root, query, max_results, rg_path))
        return expected

    monkeypatch.setattr(search_tools.shutil, "which", lambda _: "/usr/bin/rg")
    monkeypatch.setattr(search_tools, "_search_with_ripgrep", fake_rg)

    assert search_code(tmp_path, "target", max_results=5) == expected
    assert calls == [(tmp_path.resolve(), "target", 5, "/usr/bin/rg")]


def test_search_code_rejects_invalid_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        search_code(tmp_path, "", max_results=10)

    with pytest.raises(ValueError):
        search_code(tmp_path, "target", max_results=0)

    with pytest.raises(FileNotFoundError):
        search_code(tmp_path / "missing", "target", max_results=10)
