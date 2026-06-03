from __future__ import annotations

from app.evals.metrics import EvalResult
from app.evals.scenarios import EvalScenario


def render_eval_report(
    scenarios: list[EvalScenario],
    results: list[EvalResult],
) -> str:
    result_by_id = {result.scenario_id: result for result in results}
    lines = [
        "# Agentrail Evaluation Report",
        "",
        "This report summarizes deterministic project-specific evals for Agentrail.",
        "No LLM-as-judge is used in this phase.",
        "",
        "## Coverage",
        "",
        "- Repository scanning",
        "- Code search relevance",
        "- Line-numbered evidence extraction",
        "- Evidence-grounded root cause text",
        "- Optional fix strategy grounding",
        "- Patch preview file grounding",
        "- Approval interrupt behavior",
        "- Test result handling",
        "- Verifier status",
        "- Risk scorer level",
        "- Final report sections",
        "",
        "## Scenario Results",
        "",
    ]

    for scenario in scenarios:
        result = result_by_id.get(scenario.id)
        if result is None:
            lines.append(f"- {scenario.name}: not run")
            continue
        status = "pass" if result.passed else "fail"
        lines.append(f"- {scenario.name}: {status}, {result.score}/100")

    lines.extend(
        [
            "",
            "## Metric Definitions",
            "",
            "- `repo_scanned`: repository scan output exists.",
            "- `relevant_files_found`: expected files appear in search or evidence.",
            "- `evidence_found`: evidence has line numbers and expected keywords.",
            "- `root_cause_grounded`: root cause includes expected keywords and evidence file references.",
            "- `fix_strategy_grounded`: fix strategy target files are evidence-backed when present.",
            "- `patch_file_valid`: patch preview files match expected evidence-backed files.",
            "- `approval_required`: approval interrupt was observed when expected.",
            "- `test_result_valid`: allowed, skipped, failed, or blocked commands are represented correctly.",
            "- `verification_status_valid`: verifier status matches scenario expectation.",
            "- `risk_level_valid`: risk level matches scenario expectation.",
            "- `report_sections_present`: final report includes required sections.",
            "",
            "## How To Run",
            "",
            "```bash",
            "cd backend",
            "uv run python -m app.evals.runner",
            "```",
            "",
            "## Current Limitations",
            "",
            "- This is not SWE-bench.",
            "- Scenarios are small project-specific regression fixtures.",
            "- Metrics are deterministic string/structure checks, not semantic judges.",
            "- No real OpenAI, GitHub, or E2B credentials are required.",
            "- Private repository behavior is not evaluated.",
            "- Patch application is not evaluated because Agentrail only creates patch previews.",
        ],
    )
    return "\n".join(lines)
