# Agentrail Roadmap

## Completed

- Repo scanner
- Code search
- Evidence reader
- LLM root cause
- LLM fix strategy
- Patch preview
- Human approval
- Local safe runner
- E2B adapter
- Verifier
- Risk scorer
- Timeline API
- Graph UI
- GitHub import
- Evaluation suite
- GitHub issue import
- PR draft export

## Evaluation Suite

Implemented as a small deterministic project-specific regression suite. It measures root cause quality, patch preview behavior, verification correctness, risk scoring, and report quality across local fixtures.

Suggested evaluation dimensions:

- Evidence relevance
- Root-cause accuracy
- Fix-strategy usefulness
- Patch-preview minimality
- Verification correctness
- Risk score calibration
- Final report usefulness

Run:

```bash
cd backend
uv run python -m app.evals.runner
```

## GitHub Issue Import

Implemented as read-only public GitHub issue import. Users can paste an issue URL and prefill task description, expected behavior hints, labels, issue metadata, and repo context.

MVP boundaries:

- Public issues first.
- No issue comments posted automatically.
- No private repository or organization support until authentication and permissions are designed.

## PR Draft Export

Implemented as copy-ready draft export. It generates PR title, PR description, test evidence, risk summary, rollback plan, and review checklist.

MVP boundary:

- Do not open PRs automatically.
- Export draft text only.
- Keep human review and repository write control outside Agentrail.

## Final MVP Status

Agentrail is complete for the original portfolio goal after Phase 28.

## Post-MVP Ideas

- Durable LangGraph checkpointer
- Real PR creation
- Deeper CI integration
- Multi-language support
- Benchmark dashboard
