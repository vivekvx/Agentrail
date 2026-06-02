from __future__ import annotations

from pathlib import Path

import pytest

from app.tools.path_policy import (
    is_excluded_secret_file,
    validate_repo_directory,
)


def test_validate_repo_directory_resolves_existing_directory(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    result = validate_repo_directory(repo, allowed_roots=[tmp_path])

    assert result == repo.resolve()


def test_validate_repo_directory_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_repo_directory(tmp_path / "missing", allowed_roots=[tmp_path])


def test_validate_repo_directory_rejects_file_when_directory_expected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hello\n", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        validate_repo_directory(file_path, allowed_roots=[tmp_path])


def test_validate_repo_directory_rejects_path_outside_allowed_roots(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()

    with pytest.raises(PermissionError):
        validate_repo_directory(outside_root, allowed_roots=[allowed_root])


@pytest.mark.parametrize(
    "file_name",
    [
        ".env",
        ".env.local",
        "secrets.json",
        "private.pem",
        "deploy.key",
    ],
)
def test_is_excluded_secret_file(file_name: str) -> None:
    assert is_excluded_secret_file(Path(file_name)) is True


def test_is_excluded_secret_file_allows_normal_source_files() -> None:
    assert is_excluded_secret_file(Path("app/main.py")) is False
