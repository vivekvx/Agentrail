# Agentrail Evaluation Report

Phase 26 adds a deterministic evaluation suite for Agentrail.

This is not SWE-bench. It is a small project-specific regression suite that checks whether the Agentrail workflow behaves correctly across controlled local scenarios.

## What Evaluation Covers

- Repository scanning
- Code search relevance
- Line-numbered evidence extraction
- Evidence-grounded root cause text
- Optional fix strategy grounding
- Patch preview file grounding
- Approval interrupt behavior
- Test result handling for allowed, skipped, failed, and blocked commands
- Verifier status
- Risk scorer level
- Final report sections

## Scenario List

- `auth-refresh-bug`: React auth token persistence fixture that should generate an evidence-backed patch preview.
- `missing-env-handling`: FastAPI environment-variable fixture with no deterministic patch preview.
- `frontend-build-failure`: frontend fixture with a deterministic failing `npm run build` command.
- `no-patch-needed`: documentation-only fixture where no patch preview is expected.
- `unsafe-command-request`: unsafe command fixture that should be blocked by command policy.

## Current Local Output

Generated with:

```bash
cd backend
uv run python -m app.evals.runner
```

```text
PASS Auth refresh token persistence: 100/100
PASS Missing environment handling: 100/100
PASS Frontend build failure: 100/100
PASS No patch needed: 100/100
PASS Unsafe command request: 100/100
```

## Metric Definitions

- `repo_scanned`: repository scan output exists.
- `relevant_files_found`: expected files appear in search or evidence.
- `evidence_found`: evidence has line numbers and expected keywords.
- `root_cause_grounded`: root cause includes expected keywords and evidence file references.
- `fix_strategy_grounded`: fix strategy target files are evidence-backed when present.
- `patch_file_valid`: patch preview files match expected evidence-backed files.
- `approval_required`: approval interrupt was observed when expected.
- `test_result_valid`: allowed, skipped, failed, or blocked commands are represented correctly.
- `verification_status_valid`: verifier status matches scenario expectation.
- `risk_level_valid`: risk level matches scenario expectation.
- `report_sections_present`: final report includes required sections.

## How To Run Evals

```bash
cd backend
uv run python -m app.evals.runner
```

Run eval tests:

```bash
cd backend
PYTHONDONTWRITEBYTECODE=1 uv run --isolated --extra dev pytest -p no:cacheprovider tests/test_evals.py
```

## Current Limitations

- No LLM-as-judge is used.
- No real OpenAI, GitHub, or E2B credentials are required.
- The suite uses small local fixtures, not broad benchmark repositories.
- Patch application is not evaluated because Agentrail generates patch previews only.
- Private GitHub repository flows are not evaluated.
- Risk score expectations are coarse and deterministic.
