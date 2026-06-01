from __future__ import annotations

from pathlib import Path

import pytest

from app.tools.file_tools import FileSnippet, read_text_file


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_read_text_file_returns_line_numbered_snippet(tmp_path: Path) -> None:
    write_file(
        tmp_path / "app" / "main.py",
        "line one\nline two\nline three\nline four\n",
    )

    result = read_text_file(
        repo_root=tmp_path,
        file_path=tmp_path / "app" / "main.py",
        start_line=2,
        end_line=3,
    )

    assert result == FileSnippet(
        file_path="app/main.py",
        start_line=2,
        end_line=3,
        lines=[
            "2: line two",
            "3: line three",
        ],
    )


def test_read_text_file_defaults_to_whole_file(tmp_path: Path) -> None:
    write_file(tmp_path / "README.md", "alpha\nbeta\n")

    result = read_text_file(repo_root=tmp_path, file_path="README.md")

    assert result.start_line == 1
    assert result.end_line == 2
    assert result.lines == [
        "1: alpha",
        "2: beta",
    ]


def test_read_text_file_enforces_max_file_size(tmp_path: Path) -> None:
    write_file(tmp_path / "large.txt", "abcdef")

    with pytest.raises(ValueError, match="exceeds max file size"):
        read_text_file(
            repo_root=tmp_path,
            file_path="large.txt",
            max_file_size_bytes=5,
        )


@pytest.mark.parametrize(
    "file_name",
    [
        ".env",
        ".env.local",
        "prod.secret",
        "credentials.json",
        "api_key.txt",
        "service-token.txt",
    ],
)
def test_read_text_file_blocks_secret_looking_files(
    tmp_path: Path,
    file_name: str,
) -> None:
    write_file(tmp_path / file_name, "SECRET=value\n")

    with pytest.raises(PermissionError, match="secret-looking file"):
        read_text_file(repo_root=tmp_path, file_path=file_name)


def test_read_text_file_blocks_files_outside_repo_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")

    with pytest.raises(PermissionError, match="outside repo root"):
        read_text_file(repo_root=tmp_path, file_path=outside)


def test_read_text_file_rejects_invalid_line_range(tmp_path: Path) -> None:
    write_file(tmp_path / "app.py", "one\ntwo\n")

    with pytest.raises(ValueError, match="start_line"):
        read_text_file(repo_root=tmp_path, file_path="app.py", start_line=0)

    with pytest.raises(ValueError, match="end_line"):
        read_text_file(
            repo_root=tmp_path,
            file_path="app.py",
            start_line=2,
            end_line=1,
        )
