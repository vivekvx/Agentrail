# DevPilot Verify Demo Script

## 2-Minute Demo

One-sentence problem:

> AI coding tools can produce patches fast, but engineering teams still need evidence, approval, verification, and risk reporting before trusting a fix.

Script:

1. Open the dashboard and create a run with a public GitHub issue URL, public repository URL, or local repository path.
2. If using an issue URL, show how the issue title/body prefill the task and repo context. If using a repo/path, enter a concrete bug description and expected behavior manually.
3. Start the run and show the event timeline as the agent scans the repo, searches code, gathers evidence, and produces root-cause analysis.
4. Open the run detail view and point out line-numbered evidence and the generated fix strategy.
5. Show the patch preview and approval card. Emphasize that DevPilot Verify does not apply the patch to the original repository.
6. Approve the patch preview so the workflow can continue into verification.
7. Show the test result, verifier output, and risk score.
8. Show the final report.
9. Open PR Draft, copy the title/body, and explain that this is safe because it does not write to GitHub.

Closing line:

> DevPilot Verify packages the responsible engineering loop around AI-generated fixes: inspect, prove, approve, verify, score risk, and report.

## 5-Minute Demo

1. Start with the architecture:
   - Next.js frontend
   - FastAPI API
   - LangGraph workflow
   - repository tools
   - optional structured LLM provider
   - local or E2B test runner
   - verifier, risk scorer, report generator
2. Show repository input:
   - Use a local path for deterministic demos.
   - Use a public GitHub repository URL when demonstrating import.
   - Use a public GitHub issue URL when demonstrating issue-to-analysis workflow.
   - Mention private GitHub repository support is outside the MVP.
3. Show issue import:
   - Issue URL is parsed into owner, repo, and issue number.
   - GitHub issue title, body, labels, state, author, and timestamps are fetched read-only.
   - Repo URL is inferred from the issue unless already provided.
4. Show the timeline:
   - Run created
   - Run started
   - Repository scanned
   - Code searched
   - Evidence gathered
   - Root cause generated
   - Patch preview generated
   - Pending approval
5. Show evidence-backed root cause:
   - Highlight file paths and line-numbered snippets.
   - Explain that search results become evidence only after relevant files are inspected.
6. Show fix strategy:
   - Explain that structured LLM fix strategy is optional.
   - Mention deterministic fallback keeps local development and tests stable.
7. Show approval interrupt:
   - The workflow pauses before verification continues.
   - Approval or rejection is explicit and persisted.
8. Show test runner:
   - Local safe runner is default.
   - E2B sandbox runner is optional and requires configuration.
   - Only allowlisted commands run.
9. Show verification and risk:
   - Verifier checks approval, patch preview, evidence, and tests.
   - Risk scorer explains remaining uncertainty.
10. Show graph view:
   - The visual graph maps the same workflow nodes as the backend.
11. End on final report:
   - Summary
   - Evidence
   - Root cause
   - Fix strategy
   - Patch diff
   - Test results
   - Verification
   - Risk score
   - Next step
12. Show PR draft export:
   - Generate PR Draft.
   - Review title and Markdown body.
   - Copy the draft into a manual PR description.
   - Emphasize that DevPilot Verify does not open a PR or write to GitHub.

## Interview Talking Points

- Verification-first matters because AI output can be plausible without being correct. DevPilot Verify forces the system to collect evidence before reporting confidence.
- The agent is not fully autonomous because repository changes still need human review. The MVP generates patch previews and preserves review control.
- Human approval is required so a user can inspect the root cause, evidence, patch diff, and risk before the workflow continues.
- Structured LLM output is safer than free text because fields can be validated, persisted, and rendered consistently. Deterministic fallbacks keep tests stable.
- E2B is optional because local development should work without cloud credentials. Teams can enable sandboxing when they want stronger isolation.
- The next high-value work is an evaluation suite that measures root-cause quality, evidence relevance, patch-preview quality, verification correctness, and risk calibration.

## Demo Risks

- The local runner does not apply a patch to the original repository.
- E2B requires an API key when enabled.
- LLM features are optional and disabled by default for deterministic local behavior.
- Private GitHub repository support is not included in this MVP.
- GitHub issue import is read-only; DevPilot Verify does not comment, close issues, or open PRs.
- PR Draft Export is copy-only; it does not push branches, commit code, or create GitHub PRs.
- The project is portfolio-ready, but not claimed as production-ready.
