from __future__ import annotations

from app.agents.state import AgentRunState


def patch_generator_node(state: AgentRunState) -> dict[str, object]:
    # Prefer LLM fix strategy when available.
    fix_strategy = state.get("fix_strategy")
    if isinstance(fix_strategy, dict) and fix_strategy.get("target_files"):
        diff = _stub_diff_from_fix_strategy(
            fix_strategy,
            state.get("evidence", []),
        )
        if diff:
            return {"patch_diff": diff}

    # Fallback: legacy hardcoded auth patch for demo purposes.
    evidence = state.get("evidence", [])
    file_path = _auth_context_path_with_token_persistence(evidence)
    if file_path is not None:
        return {"patch_diff": _auth_refresh_patch(file_path)}

    return {}


def _stub_diff_from_fix_strategy(
    fix_strategy: dict[str, object],
    evidence: list[dict[str, object]],
) -> str:
    """Generate a human-readable stub diff from LLM fix strategy output.

    Shows the change plan as comment lines so developers know what to edit.
    Not a syntactically perfect patch — Apply Patch dry-run will reject it,
    which is intentional: developer applies manually using this as a guide.
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

    # Evidence snippet map: file_path -> first snippet
    snippets: dict[str, str] = {}
    for item in evidence:
        fp = item.get("file_path")
        snip = item.get("snippet")
        if isinstance(fp, str) and isinstance(snip, str) and fp not in snippets:
            snippets[fp] = snip

    lines: list[str] = []
    lines.append(f"# Fix strategy: {summary}")
    lines.append(f"# Confidence: {confidence}")
    lines.append("#")
    if change_plan:
        lines.append("# Change plan:")
        for step in change_plan:
            lines.append(f"#   - {step}")
    lines.append("")

    for file_path in target_files:
        lines.append(f"diff --git a/{file_path} b/{file_path}")
        lines.append(f"--- a/{file_path}")
        lines.append(f"+++ b/{file_path}")
        lines.append("@@ -1,0 +1,0 @@")
        snippet = snippets.get(file_path)
        if snippet:
            for snip_line in snippet.splitlines()[:6]:
                lines.append(f" {snip_line}")
        for step in change_plan[:4]:
            lines.append(f"+# TODO: {step}")
        lines.append("")

    return "\n".join(lines)


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
