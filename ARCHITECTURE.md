# ARCHITECTURE.md

# DevPilot Verify Architecture

## System Overview

DevPilot Verify is organized around a verification-first agent workflow. The system should keep orchestration, repository analysis, patch generation, verification, persistence, and user interaction as separate concerns.

Target stack:

- FastAPI backend for APIs and orchestration entry points
- LangGraph for workflow state and agent transitions
- Pydantic v2 for typed contracts
- PostgreSQL and SQLAlchemy for persistence
- Next.js and React for the web UI
- `ripgrep` and Probe-style search for repository investigation
- E2B sandbox execution in a later phase
- Optional LangSmith tracing
- DeepEval evaluation in a later phase

## High-Level Components

```text
Next.js UI
  -> FastAPI API
    -> LangGraph workflow
      -> repo scanner
      -> search service
      -> evidence service
      -> root cause analyzer
      -> patch proposer
      -> approval gate
      -> sandbox verifier
      -> risk scorer
      -> report generator
    -> PostgreSQL persistence
```

## Backend Responsibilities

The FastAPI backend should expose workflow-oriented APIs rather than low-level model calls.

Primary responsibilities:

- Create and track verification tasks.
- Start repository scans.
- Advance LangGraph workflow runs.
- Store evidence, patch proposals, approvals, verification results, and final reports.
- Serve structured state to the frontend.
- Enforce approval before patch application.

The backend should avoid mixing HTTP route logic with agent reasoning or repository tool logic.

## Frontend Responsibilities

The Next.js frontend should make the workflow inspectable and controllable.

Primary responsibilities:

- Create a new verification task.
- Show repository scan results.
- Display the investigation plan.
- Let users inspect evidence.
- Show proposed diffs before application.
- Collect approval or rejection.
- Display verification command results.
- Present final reports and risk scoring.

The UI should prioritize clarity over chat-like magic. Users should be able to see why the agent believes something.

## LangGraph Workflow

The LangGraph workflow should model each major step explicitly:

```text
RepoScan
Planning
CodeSearch
EvidenceExtraction
RootCauseAnalysis
PatchDiff
ApprovalGate
SandboxTest
Verification
RiskScoring
FinalReport
```

Each node should receive and emit structured Pydantic v2 state. Nodes should be replayable where practical and should record tool inputs and outputs needed for audit.

## Domain Records

The persistence model should eventually include records equivalent to:

- Task: user request, repository reference, status, timestamps
- Repo scan: detected stack, files, commands, package managers
- Plan: investigation strategy, assumptions, verification approach
- Search result: query, tool, matched files, matched locations
- Evidence: source, location, observed fact, confidence, related task
- Root cause: conclusion, supporting evidence, alternatives, confidence
- Patch proposal: diff, changed files, rationale, approval status
- Approval: approver, decision, timestamp, comments
- Verification run: command, environment, exit code, stdout, stderr
- Risk score: score, factors, mitigations, recommendation
- Final report: summary, verification status, residual risk, follow-ups

These names are conceptual. Future implementation should choose concrete table and model names that fit the codebase.

## Repository Search

Search should be tool-driven and recorded.

Initial strategy:

- Use `ripgrep` for fast literal and regex search.
- Capture query strings, working directory, included and excluded paths, and matched files.
- Use Probe-style structural search where symbol or AST-aware discovery is needed.
- Preserve enough search metadata to explain how evidence was found.

Search results are not evidence by themselves. Evidence should be extracted from inspected source, tests, logs, or command output.

## Patch Safety

Patch generation and patch application are separate stages.

Rules:

- Generate minimal diffs.
- Explain every changed file.
- Require approval before applying meaningful changes.
- Store the proposed diff even if rejected.
- Store the applied diff after approval.
- Verify after application.

The agent should not treat a patch as successful until verification has run or the final report clearly states that verification was unavailable.

## Sandbox Verification

Sandbox verification is planned for a later phase with E2B.

The architecture should allow command execution behind an interface so local execution and sandbox execution can share a common result shape:

- Command
- Working directory
- Environment summary
- Exit code
- Stdout
- Stderr
- Duration
- Artifacts

## Risk Scoring

Risk scoring should combine structured signals:

- Test coverage for touched behavior
- Verification command results
- Number and sensitivity of changed files
- Confidence in root cause
- Amount of inference versus direct evidence
- Framework or dependency uncertainty
- Known unverified areas

Risk scores should be explainable. A numeric score without factors is not useful.

## Observability

LangSmith is optional and should be introduced behind configuration.

Traceable events should include:

- Workflow node start and finish
- Tool calls
- Search queries
- Evidence extraction
- Patch proposal
- Approval decision
- Verification commands
- Final report generation

The system should still work without LangSmith.

## Evaluation

DeepEval is planned for later workflow evaluation.

Candidate evaluation dimensions:

- Correct root cause identification
- Evidence relevance
- Patch minimality
- Verification completeness
- Risk score calibration
- Final report usefulness

Evaluation should use fixed repository fixtures and expected outcomes once implementation begins.

## Security Considerations

- Treat repository contents as untrusted.
- Treat model output as untrusted.
- Do not execute repository commands outside an approved execution path.
- Avoid exposing secrets from environment files, logs, or command output.
- Keep approval records for patch application.
- Prefer isolated execution for tests and package scripts.

