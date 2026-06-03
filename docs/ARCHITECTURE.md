# Agentrail Architecture

## System Overview

Agentrail is a verification-first AI software engineering agent. It is structured as a local/portfolio MVP with production-minded safety boundaries: the backend orchestrates a LangGraph workflow, the frontend renders an inspectable developer dashboard, and repository tools collect evidence before any fix is trusted.

```text
Next.js UI
-> FastAPI API
-> LangGraph workflow
-> repository tools
-> optional LLM provider
-> patch preview
-> approval interrupt
-> test runner
-> verifier
-> risk scorer
-> final report + timeline
```

## Backend Modules

- `app/main.py`: FastAPI app entry point.
- `app/api/routes_runs.py`: run creation, start, approval, rejection, read, and event APIs.
- `app/agents/graph.py`: LangGraph workflow definition.
- `app/agents/nodes/*`: planner, scanner, search, evidence, root cause, fix strategy, patch generator, approval, test runner, verifier, risk scorer, reporter.
- `app/tools/*`: repository scanning, search, file access, path policy, GitHub URL validation, and test command execution.
- `app/services/*`: run event persistence, repository import, optional LLM provider, optional E2B sandbox adapter.
- `app/db/*`: SQLAlchemy engine, session, and persistence models.
- `app/schemas/*`: Pydantic API schemas.

## Frontend Modules

- `src/app/page.tsx`: dashboard route.
- `src/app/runs/[id]/page.tsx`: run detail route.
- `src/app/runs/[id]/graph/page.tsx`: graph view route.
- `src/app/api/agentrail/[...path]/route.ts`: frontend proxy to backend API.
- `src/components/create-run-form.tsx`: run creation.
- `src/components/agent-timeline.tsx`: event timeline.
- `src/components/execution-graph-panel.tsx`: visual workflow graph.
- `src/components/approval-card.tsx`: approval/rejection controls.
- `src/components/patch-preview-card.tsx`: patch diff rendering.
- `src/components/run-analysis-panels.tsx`: test result, verification, and risk panels.
- `src/components/final-report-card.tsx`: final report rendering.

## LangGraph Pipeline

```text
START
-> planner
-> repo_scanner
-> code_search
-> evidence_reader
-> root_cause
-> fix_strategy
-> patch_generator
-> approval_node
-> test_runner
-> verifier
-> risk_scorer
-> reporter
-> END
```

Each node reads and writes structured `AgentRunState`. The approval node can interrupt the graph and resume later with an approve or reject decision.

## API Lifecycle

```text
POST /api/runs
-> persist created run
-> log run_created

POST /api/runs/{run_id}/start
-> resolve local path or import public GitHub repo
-> invoke LangGraph
-> persist graph state
-> either return pending_approval or completed
-> log timeline events

POST /api/runs/{run_id}/approve
-> resume LangGraph after approval interrupt
-> run tests
-> verify
-> score risk
-> generate report

POST /api/runs/{run_id}/reject
-> resume graph with rejection
-> generate final report without running tests
```

## Data Model Summary

- `AgentRun`: repository source, user task, expected behavior, test command, status, current node, thread ID, approval payload/status, fix strategy, patch diff, test result, verification result, risk score, final report, error message, timestamps.
- `RunEvent`: run ID, event type, title, optional message, JSON payload, timestamp.

JSON fields are persisted as text and loaded into structured response objects at the API boundary.

## Event Timeline Model

The API logs user-visible run events such as:

- `run_created`
- `run_started`
- `repo_import_started`
- `repo_import_completed`
- `repo_scanned`
- `code_searched`
- `evidence_read`
- `root_cause_generated`
- `patch_generated`
- `pending_approval`
- `approved`
- `rejected`
- `tests_run`
- `verified`
- `risk_scored`
- `report_generated`
- `run_completed`
- `run_failed`

Timeline payloads are sanitized and should not include API keys, raw tracebacks, or secret file contents.

## Test Runner Architecture

```text
test_runner node
-> approval_status == approved?
-> test_command present?
-> choose provider
   -> local safe runner by default
   -> E2B runner only when enabled and configured
-> return common SandboxTestResult shape
```

The common result shape includes provider, command, status, exit code, stdout, stderr, duration, optional sandbox ID, and optional error message.

Local runner safety:

- Uses the shared allowlist.
- Runs commands with `shell=False`.
- Executes inside the validated repository directory.
- Captures stdout, stderr, exit code, and duration.

## Optional LLM Architecture

Structured LLM analysis is optional and behind configuration:

```text
evidence + task context
-> LLM provider
-> structured root-cause or fix-strategy response
-> schema validation
-> deterministic fallback when disabled or unavailable
```

The root-cause and fix-strategy nodes can produce useful local output without an external API key.

## Optional E2B Architecture

```text
validated repo path
-> safe tar archive
-> exclude secrets/heavy folders
-> lazy import E2B SDK
-> create sandbox
-> upload archive
-> extract into sandbox workspace
-> run allowlisted command
-> capture result
-> terminate sandbox
```

E2B is optional. Missing SDK or missing API key returns a clean error result without exposing secrets.
