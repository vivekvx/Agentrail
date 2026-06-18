from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.core.config import get_settings
from app.services.repo_map import build_module_graph


class TourError(RuntimeError):
    """Raised when a tour cannot be generated."""


def _prompt(name: str, languages: list[dict], graph: dict) -> str:
    modules = ", ".join(
        f"{n['label']} ({n['files']} files, {n['lang'] or 'mixed'})"
        for n in graph["nodes"]
        if n["depth"] > 0
    )
    langs = ", ".join(f"{lang['name']}" for lang in languages[:6])
    return (
        f"You are onboarding a new engineer to the codebase '{name}'.\n"
        f"Languages: {langs or 'unknown'}.\n"
        f"Top modules: {modules or 'none'}.\n\n"
        "Produce a guided tour as JSON with this exact shape:\n"
        '{"steps": [{"title": "...", "path": "module/or/file", '
        '"explanation": "1-2 sentences"}]}\n'
        "Give 4 to 6 steps, ordered so a newcomer reads them top to bottom: "
        "start at the entry point, then core logic, then supporting modules. "
        "Use module names from the list for 'path'. Return only JSON."
    )


def generate_tour(name: str, languages: list[dict], tree: dict | None) -> list[dict]:
    """Ask Ollama for an ordered onboarding tour. Returns a list of steps.

    ponytail: trusts the model for step content; paths come from the module
    list but aren't verified against the tree. Add path-existence validation
    if models start hallucinating files.
    """
    settings = get_settings()
    graph = build_module_graph(tree)
    body = json.dumps(
        {
            "model": settings.ollama_model,
            "prompt": _prompt(name, languages, graph),
            "format": "json",
            "stream": False,
        }
    ).encode()

    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.ollama_timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TourError(f"Could not reach Ollama at {settings.ollama_base_url}: {exc}")

    return _parse_steps(payload.get("response", ""))


def _parse_steps(raw: str) -> list[dict]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise TourError("Model did not return valid JSON")

    steps = data.get("steps") if isinstance(data, dict) else data
    if not isinstance(steps, list) or not steps:
        raise TourError("Model returned no steps")

    cleaned: list[dict] = []
    for s in steps:
        if not isinstance(s, dict) or not s.get("title"):
            continue
        cleaned.append(
            {
                "title": str(s["title"])[:200],
                "path": str(s.get("path", ""))[:300],
                "explanation": str(s.get("explanation", ""))[:600],
            }
        )
    if not cleaned:
        raise TourError("Model returned no usable steps")
    return cleaned
