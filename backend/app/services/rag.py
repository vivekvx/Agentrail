from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from pathlib import Path

from app.core.config import get_settings

# Extensions worth embedding for code Q&A (text/code only).
_TEXT_EXT = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".sql",
    ".css",
    ".scss",
    ".html",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
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
_MAX_FILE_BYTES = 200_000


class RagError(RuntimeError):
    """Raised when chat indexing or answering fails."""


def chunk_text(text: str, size: int) -> list[str]:
    """Split text into ~size-char chunks on line boundaries."""
    chunks: list[str] = []
    buf: list[str] = []
    length = 0
    for line in text.splitlines(keepends=True):
        buf.append(line)
        length += len(line)
        if length >= size:
            chunks.append("".join(buf))
            buf, length = [], 0
    if buf:
        chunks.append("".join(buf))
    return [c for c in chunks if c.strip()]


def _collect_chunks(root: Path, chunk_chars: int, max_chunks: int) -> list[dict]:
    out: list[dict] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
        for f in sorted(files):
            if Path(f).suffix.lower() not in _TEXT_EXT:
                continue
            fp = Path(current) / f
            try:
                if fp.stat().st_size > _MAX_FILE_BYTES:
                    continue
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(fp.relative_to(root))
            for chunk in chunk_text(text, chunk_chars):
                out.append({"path": rel, "text": chunk})
                if len(out) >= max_chunks:
                    return out
    return out


def _embed(text: str) -> list[float]:
    settings = get_settings()
    body = json.dumps({"model": settings.ollama_embed_model, "prompt": text}).encode()
    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.ollama_timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RagError(f"Could not reach Ollama: {exc}")
    vec = data.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise RagError("Ollama returned no embedding")
    return vec


def build_index(root: Path) -> list[dict]:
    """Chunk + embed a cloned repo. Returns [{path, text, vec}]. Best-effort
    caller catches RagError (e.g. Ollama down) and leaves the repo unindexed."""
    settings = get_settings()
    chunks = _collect_chunks(root, settings.rag_chunk_chars, settings.rag_max_chunks)
    for c in chunks:
        c["vec"] = _embed(c["text"])
    return chunks


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def answer(question: str, index: list[dict]) -> dict:
    """Embed the question, retrieve top-k chunks by cosine, ask Ollama."""
    settings = get_settings()
    if not index:
        raise RagError("Repository is not indexed for chat")
    qvec = _embed(question)
    ranked = sorted(index, key=lambda c: _cosine(qvec, c["vec"]), reverse=True)
    top = ranked[: settings.rag_top_k]

    context = "\n\n".join(f"# {c['path']}\n{c['text']}" for c in top)
    prompt = (
        "Answer the question using only the code context below. Cite file paths "
        "you used. If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    body = json.dumps({"model": settings.ollama_model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.ollama_timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RagError(f"Could not reach Ollama: {exc}")

    sources = sorted({c["path"] for c in top})
    return {"answer": data.get("response", "").strip(), "sources": sources}
