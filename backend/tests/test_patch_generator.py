from __future__ import annotations

from app.agents.nodes.patch_generator import patch_generator_node


def test_patch_generator_skips_localstorage_evidence_without_auth_context_path() -> None:
    result = patch_generator_node(
        {
            "user_task": "Fix auth refresh",
            "root_cause": "Token persistence is not restored.",
            "evidence": [
                {
                    "file_path": "src/session.ts",
                    "start_line": 1,
                    "end_line": 2,
                    "snippet": (
                        "1: // token persistence should restore localStorage\n"
                        "2: localStorage.setItem('token', token)"
                    ),
                    "reason": "Search matched localStorage token persistence.",
                },
            ],
        },
    )

    assert "patch_diff" not in result


def test_patch_generator_uses_auth_context_evidence_path() -> None:
    result = patch_generator_node(
        {
            "user_task": "Fix auth refresh",
            "root_cause": "Token persistence is not restored.",
            "evidence": [
                {
                    "file_path": "src/AuthContext.tsx",
                    "start_line": 4,
                    "end_line": 6,
                    "snippet": (
                        "4: const [token, setToken] = useState<string | null>(null);\n"
                        "5: // token persistence should restore localStorage on refresh\n"
                        "6: localStorage.setItem('token', token ?? '')"
                    ),
                    "reason": "Search matched localStorage token persistence.",
                },
            ],
        },
    )

    patch_diff = result["patch_diff"]
    assert "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx" in patch_diff
    assert "localStorage.getItem(\"token\")" in patch_diff
