from __future__ import annotations

import ast
import difflib
import os

from app.agents.state import AgentRunState
from app.core.config import get_settings
from app.services.llm_provider import generate_patch_code

# Lines of context around the evidence range sent to the LLM patch writer.
LLM_WINDOW_PADDING = 30


def patch_generator_node(state: AgentRunState) -> dict[str, object]:
    fix_strategy = state.get("fix_strategy")
    repo_path: str | None = state.get("repo_path")
    evidence: list[dict[str, object]] = state.get("evidence", [])

    if isinstance(fix_strategy, dict) and fix_strategy.get("target_files"):
        diff = _llm_diff_from_fix_strategy(fix_strategy, evidence, repo_path, state)
        if diff:
            return {"patch_diff": diff, "patch_mode": "llm"}

        diff = _real_diff_from_fix_strategy(fix_strategy, evidence, repo_path)
        if diff:
            return {"patch_diff": diff, "patch_mode": "annotated-diff"}

    # Final fallback: hardcoded demo patch so the offline demo (no API key)
    # still shows an end-to-end run against the bundled sample repo.
    file_path = _auth_context_path_with_token_persistence(evidence)
    if file_path is not None:
        return {"patch_diff": _auth_refresh_patch(file_path), "patch_mode": "legacy-demo"}

    return {}


def _llm_diff_from_fix_strategy(
    fix_strategy: dict[str, object],
    evidence: list[dict[str, object]],
    repo_path: str | None,
    state: AgentRunState,
) -> str:
    """LLM-written patch: real code changes, validated, diffed against disk.

    Returns "" whenever the LLM is disabled or any output fails validation,
    so callers always fall back to the deterministic diff paths.
    """
    settings = get_settings()
    if not settings.llm_patch_enabled:
        return ""

    target_files = [
        f for f in (fix_strategy.get("target_files") or []) if isinstance(f, str)
    ]
    if not target_files:
        return ""

    evidence_by_file: dict[str, dict[str, object]] = {}
    for item in evidence:
        fp = item.get("file_path")
        if isinstance(fp, str) and fp not in evidence_by_file:
            evidence_by_file[fp] = item

    hunks: list[str] = []
    for rel_path in target_files:
        ev = evidence_by_file.get(rel_path)
        abs_path = _resolve_abs_path(rel_path, ev, repo_path)
        if not abs_path:
            continue
        try:
            with open(abs_path, encoding="utf-8", errors="replace") as fh:
                original_lines = fh.readlines()
        except OSError:
            continue

        ev_start, ev_end = _evidence_line_range(ev, original_lines)
        win_start = max(0, ev_start - LLM_WINDOW_PADDING)
        win_end = min(len(original_lines), ev_end + LLM_WINDOW_PADDING)
        window = "".join(original_lines[win_start:win_end])

        proposal = generate_patch_code(
            rel_path,
            window,
            win_start + 1,
            state.get("user_task", ""),
            state.get("root_cause", ""),
            fix_strategy,
            settings=settings,
        )
        if proposal is None:
            continue

        new_window_lines = proposal.new_code.splitlines(keepends=True)
        if new_window_lines and not new_window_lines[-1].endswith("\n"):
            new_window_lines[-1] += "\n"
        modified_lines = (
            original_lines[:win_start] + new_window_lines + original_lines[win_end:]
        )

        if not _valid_syntax(rel_path, "".join(modified_lines)):
            continue

        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
                lineterm="",
            )
        )
        if diff_lines:
            hunks.append("\n".join(diff_lines) + "\n")

    return "\n".join(hunks)


def _valid_syntax(rel_path: str, text: str) -> bool:
    """Cheap syntax gate before exposing an LLM patch. Python gets a real
    parse; brace languages get balance checks; everything else passes."""
    if rel_path.endswith(".py"):
        try:
            ast.parse(text)
            return True
        except SyntaxError:
            return False
    if rel_path.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".css")):
        for open_ch, close_ch in (("{", "}"), ("(", ")"), ("[", "]")):
            if text.count(open_ch) != text.count(close_ch):
                return False
    return True


def _real_diff_from_fix_strategy(
    fix_strategy: dict[str, object],
    evidence: list[dict[str, object]],
    repo_path: str | None,
) -> str:
    """Generate a real unified diff from fix strategy.

    When the actual file is readable from disk, produces a valid ``patch``-
    compatible unified diff by appending TODO annotations at the evidence
    location.  Falls back to a human-readable stub when the file cannot be
    read (e.g. no repo_path, remote repo, or file missing).
    """
    target_files: list[str] = [
        f for f in (fix_strategy.get("target_files") or []) if isinstance(f, str)
    ]
    change_plan: list[str] = [
        c for c in (fix_strategy.get("change_plan") or []) if isinstance(c, str)
    ]
    summary: str = fix_strategy.get("summary") or ""
    confidence: str = fix_strategy.get("confidence") or "unknown"

    if not target_files:
        return ""

    # Build evidence index: file_path -> evidence item
    evidence_by_file: dict[str, dict[str, object]] = {}
    for item in evidence:
        fp = item.get("file_path")
        if isinstance(fp, str) and fp not in evidence_by_file:
            evidence_by_file[fp] = item

    header_lines = [
        f"# Fix strategy: {summary}",
        f"# Confidence: {confidence}",
        "#",
    ]
    if change_plan:
        header_lines.append("# Change plan:")
        for step in change_plan:
            header_lines.append(f"#   - {step}")
    header_lines.append("")

    all_hunks: list[str] = []
    for rel_path in target_files:
        ev = evidence_by_file.get(rel_path)
        abs_path = _resolve_abs_path(rel_path, ev, repo_path)

        if abs_path and os.path.isfile(abs_path):
            hunk = _diff_file_at_evidence(abs_path, rel_path, ev, change_plan)
        else:
            hunk = _stub_hunk(rel_path, ev, change_plan)

        if hunk:
            all_hunks.append(hunk)

    if not all_hunks:
        return ""

    return "\n".join(header_lines) + "\n".join(all_hunks)


def _resolve_abs_path(
    rel_path: str,
    ev: dict[str, object] | None,
    repo_path: str | None,
) -> str | None:
    if repo_path:
        candidate = os.path.normpath(os.path.join(repo_path, rel_path))
        if os.path.isfile(candidate):
            return candidate
    if ev:
        fp = ev.get("file_path")
        if isinstance(fp, str) and os.path.isfile(fp):
            return fp
    return None


def _diff_file_at_evidence(
    abs_path: str,
    rel_path: str,
    ev: dict[str, object] | None,
    change_plan: list[str],
) -> str:
    """Read the real file and produce a valid unified diff at the evidence location."""
    try:
        with open(abs_path, encoding="utf-8", errors="replace") as fh:
            original_lines = fh.readlines()
    except OSError:
        return _stub_hunk(rel_path, ev, change_plan)

    start_0, end_0 = _evidence_line_range(ev, original_lines)

    # Proposed version: keep original block + append TODO annotations
    original_block = original_lines[start_0:end_0]
    proposed_block: list[str] = list(original_block)
    for step in change_plan[:6]:
        proposed_block.append(f"# TODO: {step}\n")

    modified_lines = original_lines[:start_0] + proposed_block + original_lines[end_0:]

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
            lineterm="",
        )
    )

    if not diff_lines:
        return _stub_hunk(rel_path, ev, change_plan)

    return "\n".join(diff_lines) + "\n"


def _evidence_line_range(
    ev: dict[str, object] | None,
    all_lines: list[str],
) -> tuple[int, int]:
    n = len(all_lines)
    if ev is None:
        return 0, min(10, n)
    start_1 = ev.get("start_line")
    end_1 = ev.get("end_line")
    start_0 = (int(start_1) - 1) if isinstance(start_1, int) else 0
    end_0 = int(end_1) if isinstance(end_1, int) else min(start_0 + 10, n)
    return max(0, start_0), min(end_0, n)


def _stub_hunk(
    rel_path: str,
    ev: dict[str, object] | None,
    change_plan: list[str],
) -> str:
    """Fallback stub when file cannot be read from disk."""
    snippet: str = ev.get("snippet", "") if ev else ""
    snippet_lines = snippet.splitlines() if snippet else []
    n_ctx = len(snippet_lines)
    n_add = len(change_plan[:6])

    lines: list[str] = [
        f"diff --git a/{rel_path} b/{rel_path}",
        f"--- a/{rel_path}",
        f"+++ b/{rel_path}",
        f"@@ -1,{n_ctx} +1,{n_ctx + n_add} @@",
    ]
    for sl in snippet_lines:
        lines.append(f" {sl}")
    for step in change_plan[:6]:
        lines.append(f"+# TODO: {step}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Legacy helpers
# ---------------------------------------------------------------------------

def _auth_context_path_with_token_persistence(
    evidence: list[dict[str, object]],
) -> str | None:
    for item in evidence:
        file_path = item.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            continue
        if file_path.endswith("AuthContext.tsx") and _references_token_persistence(item):
            return file_path
    return None


def _references_token_persistence(evidence_item: dict[str, object]) -> bool:
    evidence_text = " ".join(
        str(value)
        for value in (
            evidence_item.get("snippet"),
            evidence_item.get("reason"),
        )
        if value is not None
    ).lower()
    return (
        "localstorage" in evidence_text
        and "token" in evidence_text
        and ("persist" in evidence_text or "persistence" in evidence_text)
    )


def _auth_refresh_patch(file_path: str) -> str:
    return "\n".join(
        [
            f"diff --git a/{file_path} b/{file_path}",
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            "@@",
            "-  const [token, setToken] = useState<string | null>(null);",
            "+  const [token, setToken] = useState<string | null>(() => {",
            "+    if (typeof window === \"undefined\") {",
            "+      return null;",
            "+    }",
            "+",
            "+    return localStorage.getItem(\"token\");",
            "+  });",
            "",
        ],
    )
