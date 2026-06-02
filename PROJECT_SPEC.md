# PROJECT_SPEC.md

# DevPilot Verify Project Spec

## Summary

DevPilot Verify is a verification-first AI coding agent for FastAPI and React/Next.js repositories. It helps diagnose issues, propose minimal patches, run verification, score risk, and produce evidence-backed reports.

The product is not just a code generator. Its core value is disciplined engineering workflow: inspect first, reason from evidence, ask before changing code, verify changes, and communicate remaining risk.

## Target Users

- Engineers maintaining FastAPI backends.
- Engineers maintaining React or Next.js frontends.
- Small teams that want AI-assisted debugging and patch proposals without losing review control.
- Agentic coding workflows that require auditable reasoning and repeatable verification.

## Supported Project Types

Initial focus:

- FastAPI backend projects
- React applications
- Next.js applications
- Monorepos containing backend and frontend packages

Out of scope for the initial product:

- Mobile apps
- Desktop apps
- Infrastructure-only repositories
- Fully autonomous production deployment
- Large-scale multi-agent task farms

## Core Workflow

```text
repo scan -> planning -> code search -> evidence extraction -> root cause -> patch diff -> approval -> sandbox test -> verification -> risk scoring -> final report
```

### 1. Repo Scan

Identify project layout, languages, frameworks, package managers, test commands, configuration files, and likely entry points.

Expected output:

- Repository summary
- Detected stack
- Candidate test commands
- Important files and directories
- Unknowns that require confirmation

### 2. Planning

Create a concise plan before code changes. The plan should connect the user request to likely files, search strategy, verification strategy, and approval checkpoints.

Expected output:

- Investigation plan
- Search targets
- Verification commands
- Risks and assumptions

### 3. Code Search

Use `ripgrep` first for fast text search. Use Probe-style structural search later for language-aware discovery where text search is insufficient.

Expected output:

- Search queries used
- Files inspected
- Relevant symbols, routes, components, or tests

### 4. Evidence Extraction

Collect evidence from source files, tests, logs, configs, stack traces, and command output.

Expected output:

- Evidence records with file paths, line references, snippets or summaries, and confidence
- Distinction between observed facts and model inference

### 5. Root Cause

Explain the likely root cause only after evidence has been collected.

Optional note:

- LLM-backed root cause analysis may enrich this phase, but it should remain optional and disabled by default with deterministic fallback available for local development and tests.

Expected output:

- Root cause statement
- Supporting evidence
- Alternative explanations considered
- Confidence level

### 6. Patch Diff

Generate a minimal proposed diff. The patch should be easy to review and tied directly to the root cause.

Expected output:

- Unified diff or structured patch proposal
- Explanation of why each changed file is needed
- Tests expected to cover the change

### 7. Approval

Ask for explicit approval before applying meaningful patches.

Expected output:

- Human-readable patch summary
- Risk notes
- Approval state

### 8. Sandbox Test

Run tests in an isolated environment when available. E2B support is planned for a later phase.

Expected output:

- Environment summary
- Commands run
- Exit codes
- Captured stdout and stderr

### 9. Verification

Verify that the patch addresses the issue and does not obviously regress nearby behavior.

Expected output:

- Passing and failing commands
- Manual verification notes where applicable
- Unverified areas

### 10. Risk Scoring

Score residual risk using evidence, test coverage, touched surface area, and uncertainty.

Expected output:

- Risk score
- Risk factors
- Mitigations
- Recommendation

### 11. Final Report

Produce a concise report suitable for a PR description, issue update, or engineering handoff.

Expected output:

- Summary
- Root cause
- Patch summary
- Verification results
- Residual risk
- Follow-up recommendations

## Functional Requirements

- Accept a repository and user task as input.
- Detect FastAPI, React, and Next.js project structure.
- Build an investigation plan before patch generation.
- Search code with recorded queries.
- Extract evidence into structured records.
- Separate observed facts from inferred conclusions.
- Produce minimal patch diffs.
- Require approval before applying meaningful patches.
- Run verification commands when available.
- Produce final reports with evidence and risk scoring.

## Non-Functional Requirements

- Verification-first: no unsupported claims.
- Auditable: every conclusion should trace to evidence or be marked as inference.
- Conservative: prefer smaller patches and explicit uncertainty.
- Secure: treat repo contents, logs, and model output as untrusted.
- Extensible: make room for additional frameworks, sandboxes, and evaluators later.
- Developer-friendly: reports should be concise and actionable.

## Explicit Non-Goals

- No fully autonomous production changes.
- No hidden patch application.
- No broad refactors unless requested.
- No dependency upgrades unless required by the task.
- No claims of correctness without verification evidence.

## Success Metrics

- Percentage of reports with cited evidence.
- Percentage of patches with successful verification commands.
- Human approval rate for proposed diffs.
- Regression rate after accepted patches.
- Time from request to evidence-backed patch proposal.
- False root cause rate during evaluation.

## Future Integrations

- E2B for isolated repository execution.
- LangSmith for trace inspection and workflow observability.
- DeepEval for regression and quality evaluation of agent behavior.
- Probe for structural code search beyond text matching.
