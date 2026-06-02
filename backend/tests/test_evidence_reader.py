from __future__ import annotations

from pathlib import Path

from app.agents.nodes.evidence_reader import evidence_reader_node


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_evidence_reader_skips_unsafe_search_results(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    write_file(outside, "target outside repo\n")
    write_file(tmp_path / "large.py", "target\n" * 300_000)
    write_file(tmp_path / "safe.py", "target inside repo\n")

    result = evidence_reader_node(
        {
            "repo_path": str(tmp_path),
            "search_results": [
                {
                    "file_path": str(outside),
                    "line_number": 1,
                    "matched_line": "target outside repo",
                    "score": 1,
                },
                {
                    "file_path": "large.py",
                    "line_number": 1,
                    "matched_line": "target",
                    "score": 1,
                },
                {
                    "file_path": "safe.py",
                    "line_number": 1,
                    "matched_line": "target inside repo",
                    "score": 1,
                },
            ],
        },
    )

    assert result["evidence"] == [
        {
            "file_path": "safe.py",
            "start_line": 1,
            "end_line": 1,
            "snippet": "1: target inside repo",
            "reason": "Search matched line 1: target inside repo",
        },
    ]
