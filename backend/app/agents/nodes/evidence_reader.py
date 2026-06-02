from __future__ import annotations

from app.agents.state import AgentRunState
from app.tools.file_tools import FileSnippet, read_text_file


MAX_EVIDENCE_FILES = 3
SNIPPET_CONTEXT_LINES = 1


def evidence_reader_node(state: AgentRunState) -> dict[str, object]:
    repo_path = state["repo_path"]
    evidence: list[dict[str, object]] = []

    for search_result in _top_search_results(state.get("search_results", [])):
        file_path = search_result["file_path"]
        line_number = search_result["line_number"]
        matched_line = search_result["matched_line"]
        start_line = max(1, line_number - SNIPPET_CONTEXT_LINES)
        end_line = line_number + SNIPPET_CONTEXT_LINES

        try:
            snippet = read_text_file(
                repo_root=repo_path,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
            )
        except (FileNotFoundError, IsADirectoryError, PermissionError, ValueError):
            continue

        evidence.append(
            _evidence_item(
                snippet=snippet,
                matched_line=matched_line,
                line_number=line_number,
            ),
        )

    return {"evidence": evidence}


def _top_search_results(search_results: list[dict[str, object]]) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    seen_files: set[str] = set()
    ranked_results = sorted(
        enumerate(search_results),
        key=lambda item: (-_score(item[1]), item[0]),
    )

    for _, result in ranked_results:
        file_path = result.get("file_path")
        line_number = result.get("line_number")
        matched_line = result.get("matched_line")
        if not isinstance(file_path, str):
            continue
        if not isinstance(line_number, int):
            continue
        if not isinstance(matched_line, str):
            continue
        if file_path in seen_files:
            continue
        seen_files.add(file_path)
        selected.append(
            {
                "file_path": file_path,
                "line_number": line_number,
                "matched_line": matched_line,
            },
        )
        if len(selected) >= MAX_EVIDENCE_FILES:
            break

    return selected


def _score(search_result: dict[str, object]) -> int:
    score = search_result.get("score")
    if not isinstance(score, int):
        return 0
    return score


def _evidence_item(
    snippet: FileSnippet,
    matched_line: str,
    line_number: int,
) -> dict[str, object]:
    return {
        "file_path": snippet.file_path,
        "start_line": snippet.start_line,
        "end_line": snippet.end_line,
        "snippet": "\n".join(snippet.lines),
        "reason": f"Search matched line {line_number}: {matched_line}",
    }
