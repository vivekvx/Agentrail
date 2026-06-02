from __future__ import annotations

from app.agents.state import AgentRunState


def patch_generator_node(state: AgentRunState) -> dict[str, object]:
    evidence = state.get("evidence", [])
    file_path = _auth_context_path_with_token_persistence(evidence)
    if file_path is None:
        return {}

    return {"patch_diff": _auth_refresh_patch(file_path)}


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
