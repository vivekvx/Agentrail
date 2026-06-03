# DevPilot Verify Project Completion

## Status

DevPilot Verify is complete for the original portfolio goal after Phase 28.

It is a local/portfolio MVP with production-minded safety design. It demonstrates a verification-first AI software engineering workflow without claiming production readiness.

## What The MVP Does

- Accepts local repository paths.
- Imports public GitHub repositories.
- Imports public GitHub issue context read-only.
- Scans repository structure.
- Searches code.
- Extracts line-numbered evidence.
- Produces deterministic or optional structured LLM root-cause analysis.
- Produces optional structured LLM fix strategy.
- Generates patch previews.
- Pauses for human approval.
- Runs allowlisted verification commands locally or through optional E2B sandboxing.
- Verifies outcome.
- Scores residual risk.
- Logs timeline events.
- Renders dashboard, timeline, graph, patch approval, verification, risk, report, and PR draft views.
- Exports copy-ready PR drafts.
- Runs deterministic project-specific evals.

## What It Intentionally Does Not Do

- Does not apply patches to the original repository.
- Does not commit code.
- Does not push branches.
- Does not create real GitHub pull requests.
- Does not comment on issues.
- Does not close or edit issues.
- Does not merge code.
- Does not require OpenAI, GitHub, or E2B credentials for local deterministic tests.
- Does not claim production readiness.

## Final Workflow

```text
repo path / repo URL / issue URL
-> scan
-> search
-> evidence
-> root cause
-> fix strategy
-> patch preview
-> approval
-> test runner
-> verifier
-> risk scorer
-> final report
-> PR draft export
```

## Safety Boundaries

- Patch preview only.
- Human approval before verification continues.
- Command allowlist.
- `shell=False` for local command runner.
- Local safe runner default.
- Optional E2B sandbox.
- Secret-like files filtered from sandbox uploads.
- GitHub issue import read-only.
- Public GitHub repository import read-only.
- Token sanitization in errors and events.
- PR draft export is copy-only.

## Remaining Post-MVP Work

- Actual PR creation behind explicit user action.
- CI integration.
- Durable LangGraph checkpointing.
- Benchmark dashboard.
- Multi-language support.
- Broader framework coverage.
- Production authentication and authorization.

## Resume Pitch

Built DevPilot Verify, a verification-first AI software engineering agent using FastAPI, LangGraph, Next.js, structured LLM outputs, optional E2B sandboxing, GitHub issue import, deterministic evals, and copy-ready PR draft export. The project wraps AI-assisted bug fixing in evidence collection, human approval, safe verification, risk scoring, and review-ready reporting.
