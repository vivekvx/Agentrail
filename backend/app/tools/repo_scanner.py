from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoScanResult:
    detected_stack: list[str]
    important_files: list[str]
    probable_frontend_directory: str | None
    probable_backend_directory: str | None
    suggested_test_commands: list[str]


STACK_ORDER = [
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

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "dist",
    "node_modules",
    "__pycache__",
}


def scan_repository(repo_path: str | Path) -> RepoScanResult:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")

    files = _list_files(root)
    relative_files = [file.relative_to(root).as_posix() for file in files]
    package_json_files = [file for file in files if file.name == "package.json"]
    requirements_files = [file for file in files if file.name == "requirements.txt"]
    pyproject_files = [file for file in files if file.name == "pyproject.toml"]
    python_files = [file for file in files if file.suffix == ".py"]
    dockerfiles = [file for file in files if file.name == "Dockerfile"]
    github_actions = [
        file
        for file in files
        if ".github/workflows/" in file.relative_to(root).as_posix()
        and file.suffix in {".yml", ".yaml"}
    ]

    package_data = {
        package_file: _read_package_json(package_file)
        for package_file in package_json_files
    }
    detected = set[str]()

    if _has_fastapi(requirements_files, pyproject_files, python_files):
        detected.add("FastAPI")
    if _has_package_dependency(package_data, "react"):
        detected.add("React")
    if _has_package_dependency(package_data, "next"):
        detected.add("Next.js")
    if _has_package_dependency(package_data, "vite") or _has_package_dependency(
        package_data,
        "@vitejs/plugin-react",
    ):
        detected.add("Vite")
    if package_json_files:
        detected.add("package.json")
    if requirements_files:
        detected.add("requirements.txt")
    if pyproject_files:
        detected.add("pyproject.toml")
    if _has_pytest(files, requirements_files, pyproject_files):
        detected.add("pytest")
    if dockerfiles:
        detected.add("Dockerfile")
    if github_actions:
        detected.add("GitHub Actions")

    frontend_directory = _probable_frontend_directory(root, package_data)
    backend_directory = _probable_backend_directory(
        root,
        requirements_files,
        pyproject_files,
        python_files,
    )

    important_files = _important_files(
        relative_files,
        detected,
    )
    suggested_test_commands = _suggested_test_commands(
        root,
        frontend_directory,
        backend_directory,
        package_data,
        "pytest" in detected,
    )

    return RepoScanResult(
        detected_stack=[name for name in STACK_ORDER if name in detected],
        important_files=important_files,
        probable_frontend_directory=frontend_directory,
        probable_backend_directory=backend_directory,
        suggested_test_commands=suggested_test_commands,
    )


def _list_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda file: file.relative_to(root).as_posix())


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _read_package_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(_read_text(path))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _has_package_dependency(
    package_data: dict[Path, dict[str, Any]],
    dependency_name: str,
) -> bool:
    for data in package_data.values():
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            dependencies = data.get(section)
            if isinstance(dependencies, dict) and dependency_name in dependencies:
                return True
    return False


def _has_fastapi(
    requirements_files: list[Path],
    pyproject_files: list[Path],
    python_files: list[Path],
) -> bool:
    for file in requirements_files + pyproject_files + python_files:
        text = _read_text(file).lower()
        if "fastapi" in text:
            return True
    return False


def _has_pytest(
    files: list[Path],
    requirements_files: list[Path],
    pyproject_files: list[Path],
) -> bool:
    if any(file.name in {"pytest.ini", "tox.ini"} for file in files):
        return True
    if any(file.name == "setup.cfg" and "pytest" in _read_text(file).lower() for file in files):
        return True
    for file in requirements_files + pyproject_files:
        text = _read_text(file).lower()
        if "pytest" in text or "[tool.pytest" in text:
            return True
    return False


def _probable_frontend_directory(
    root: Path,
    package_data: dict[Path, dict[str, Any]],
) -> str | None:
    candidates: list[tuple[int, str]] = []
    for package_file, data in package_data.items():
        score = 0
        if _package_has_dependency(data, "react"):
            score += 2
        if _package_has_dependency(data, "next"):
            score += 3
        if _package_has_dependency(data, "vite") or _package_has_dependency(
            data,
            "@vitejs/plugin-react",
        ):
            score += 2
        if score:
            directory = package_file.parent.relative_to(root).as_posix()
            candidates.append((score, "." if directory == "." else directory))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def _probable_backend_directory(
    root: Path,
    requirements_files: list[Path],
    pyproject_files: list[Path],
    python_files: list[Path],
) -> str | None:
    scores: dict[str, int] = {}
    for file in requirements_files + pyproject_files:
        text = _read_text(file).lower()
        if "fastapi" in text or "pytest" in text:
            directory = file.parent.relative_to(root).as_posix()
            scores["." if directory == "." else directory] = scores.get(directory, 0) + 2
    for file in python_files:
        if "fastapi" in _read_text(file).lower():
            directory = _backend_anchor_directory(root, file)
            scores[directory] = scores.get(directory, 0) + 3
    if not scores:
        return None
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _backend_anchor_directory(root: Path, file: Path) -> str:
    relative_parts = file.relative_to(root).parts
    if len(relative_parts) > 1:
        return relative_parts[0]
    return "."


def _important_files(relative_files: list[str], detected: set[str]) -> list[str]:
    important: list[str] = []
    for file in relative_files:
        if file == "Dockerfile":
            important.append(file)
        elif file.endswith("/Dockerfile"):
            important.append(file)
        elif file == "package.json" or file.endswith("/package.json"):
            important.append(file)
        elif file == "requirements.txt" or file.endswith("/requirements.txt"):
            important.append(file)
        elif file == "pyproject.toml" or file.endswith("/pyproject.toml"):
            important.append(file)
        elif file.startswith(".github/workflows/") and file.endswith((".yml", ".yaml")):
            important.append(file)
        elif "FastAPI" in detected and file.endswith(".py") and "main.py" in file:
            important.append(file)
    return sorted(set(important))


def _suggested_test_commands(
    root: Path,
    frontend_directory: str | None,
    backend_directory: str | None,
    package_data: dict[Path, dict[str, Any]],
    has_pytest: bool,
) -> list[str]:
    commands: list[str] = []
    if has_pytest:
        commands.append(_prefix_command(backend_directory, "python -m pytest"))

    frontend_package = _package_for_directory(root, frontend_directory, package_data)
    if frontend_package is not None:
        scripts = frontend_package.get("scripts")
        if isinstance(scripts, dict):
            if "test" in scripts:
                commands.append(_prefix_command(frontend_directory, "npm test"))
            if "lint" in scripts:
                commands.append(_prefix_command(frontend_directory, "npm run lint"))
            if "build" in scripts:
                commands.append(_prefix_command(frontend_directory, "npm run build"))
    return commands


def _package_for_directory(
    root: Path,
    directory: str | None,
    package_data: dict[Path, dict[str, Any]],
) -> dict[str, Any] | None:
    if directory is None:
        return None
    for package_file, data in package_data.items():
        package_directory = package_file.parent.relative_to(root).as_posix()
        if ("." if package_directory == "." else package_directory) == directory:
            return data
    return None


def _package_has_dependency(data: dict[str, Any], dependency_name: str) -> bool:
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        dependencies = data.get(section)
        if isinstance(dependencies, dict) and dependency_name in dependencies:
            return True
    return False


def _prefix_command(directory: str | None, command: str) -> str:
    if directory is None or directory == ".":
        return command
    return f"cd {directory} && {command}"
