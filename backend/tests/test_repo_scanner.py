from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.repo_scanner import scan_repository


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_repository_detects_fastapi_next_vite_and_project_files(
    tmp_path: Path,
) -> None:
    backend_dir = tmp_path / "backend"
    frontend_dir = tmp_path / "frontend"

    write_file(
        backend_dir / "pyproject.toml",
        """
[project]
dependencies = ["fastapi", "pytest"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""",
    )
    write_file(
        backend_dir / "app" / "main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n",
    )
    write_file(backend_dir / "requirements.txt", "fastapi\npytest\n")
    write_file(tmp_path / "Dockerfile", "FROM python:3.12\n")
    write_file(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\n")
    write_file(
        frontend_dir / "package.json",
        json.dumps(
            {
                "dependencies": {
                    "@vitejs/plugin-react": "latest",
                    "next": "latest",
                    "react": "latest",
                },
                "devDependencies": {
                    "vite": "latest",
                },
                "scripts": {
                    "build": "next build",
                    "lint": "next lint",
                    "test": "vitest",
                },
            },
        ),
    )

    result = scan_repository(tmp_path)

    assert result.detected_stack == [
        "FastAPI",
        "React",
        "Next.js",
        "Vite",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pytest",
        "Dockerfile",
        "GitHub Actions",
    ]
    assert result.probable_backend_directory == "backend"
    assert result.probable_frontend_directory == "frontend"
    assert result.important_files == [
        ".github/workflows/ci.yml",
        "Dockerfile",
        "backend/app/main.py",
        "backend/pyproject.toml",
        "backend/requirements.txt",
        "frontend/package.json",
    ]
    assert result.suggested_test_commands == [
        "cd backend && python -m pytest",
        "cd frontend && npm test",
        "cd frontend && npm run lint",
        "cd frontend && npm run build",
    ]


def test_scan_repository_detects_root_level_react_app(tmp_path: Path) -> None:
    write_file(
        tmp_path / "package.json",
        json.dumps(
            {
                "dependencies": {
                    "react": "latest",
                },
                "scripts": {
                    "build": "vite build",
                },
            },
        ),
    )

    result = scan_repository(tmp_path)

    assert result.detected_stack == ["React", "package.json"]
    assert result.probable_frontend_directory == "."
    assert result.probable_backend_directory is None
    assert result.important_files == ["package.json"]
    assert result.suggested_test_commands == [
        "npm run build",
    ]


def test_scan_repository_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_repository(tmp_path / "missing")
