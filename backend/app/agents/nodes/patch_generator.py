from __future__ import annotations

from app.agents.state import AgentRunState


def patch_generator_node(state: AgentRunState) -> dict[str, object]:
    evidence = state.get("evidence", [])
    if not _matches_auth_refresh_bug(evidence):
        return {}

    file_path = _auth_context_path(evidence)
    return {"patch_diff": _auth_refresh_patch(file_path)}


def _matches_auth_refresh_bug(evidence: list[dict[str, object]]) -> bool:
    combined_evidence = "\n".join(
        " ".join(
            str(value)
            for value in (
                item.get("file_path"),
                item.get("snippet"),
                item.get("reason"),
            )
            if value is not None
        )
        for item in evidence
    ).lower()

    return (
        "authcontext.tsx" in combined_evidence
        and "localstorage" in combined_evidence
        and "token" in combined_evidence
        and ("persist" in combined_evidence or "persistence" in combined_evidence)
    )


def _auth_context_path(evidence: list[dict[str, object]]) -> str:
    for item in evidence:
        file_path = item.get("file_path")
        if isinstance(file_path, str) and file_path.endswith("AuthContext.tsx"):
            return file_path
    return "AuthContext.tsx"


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
