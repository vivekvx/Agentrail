# ROADMAP.md

# Agentrail Roadmap

## Phase 0: Planning Foundations

Goal: define product direction, architecture, and agent instructions before implementation.

Deliverables:

- `AGENTS.md`
- `PROJECT_SPEC.md`
- `ROADMAP.md`
- `ARCHITECTURE.md`

Exit criteria:

- Future agents can understand the product scope.
- The main workflow is documented.
- Implementation phases are clear.

## Phase 1: Core Backend Skeleton

Goal: establish the FastAPI service and core domain contracts.

Planned scope:

- FastAPI application structure
- Pydantic v2 request, response, and workflow state models
- SQLAlchemy database setup for PostgreSQL
- Basic health and version endpoints
- Configuration management
- Test harness for backend services

Exit criteria:

- Backend starts locally.
- Tests run with a single documented command.
- Domain models exist for scans, evidence, patches, verification, and reports.

## Phase 2: Repository Scan And Search

Goal: inspect repositories and gather evidence before reasoning.

Planned scope:

- Repository intake abstraction
- File tree scanning
- Stack detection for FastAPI, React, and Next.js
- `ripgrep` search integration
- Probe-style structural search abstraction
- Evidence record creation

Exit criteria:

- The system can summarize a repository.
- Searches are recorded with query, files, and results.
- Evidence records can cite source locations.

## Phase 3: LangGraph Agent Workflow

Goal: implement the verification-first workflow as explicit graph states.

Planned scope:

- LangGraph nodes for scan, planning, search, evidence, root cause, patch proposal, approval, verification, risk scoring, and report generation
- State transitions with validation
- Pause point for human approval
- Trace-friendly event records

Exit criteria:

- A task can move through the workflow without applying a patch automatically.
- Approval is required before meaningful changes.
- Each stage emits structured output.

## Phase 4: Patch Proposal And Review Loop

Goal: generate minimal diffs and make them easy to inspect.

Planned scope:

- Unified diff generation
- Patch metadata
- Risk notes attached to changed files
- Approval and rejection states
- Patch application after approval

Exit criteria:

- Proposed patches are reviewable before application.
- Applied patches are tied to approval records.
- Rejected patches are retained for audit.

## Phase 5: Next.js Frontend

Goal: provide a focused UI for investigation, approval, verification, and final reporting.

Planned scope:

- Task creation view
- Repository scan summary
- Evidence browser
- Patch diff review
- Approval controls
- Verification results
- Final report view

Exit criteria:

- A user can follow the full workflow from the UI.
- Evidence and risk are visible before approval.
- Final reports are readable and exportable.

## Phase 6: Sandbox Verification

Goal: run tests and commands in isolated environments.

Planned scope:

- E2B integration
- Sandbox lifecycle management
- Command execution records
- Environment setup strategy
- Artifact capture for logs and reports

Exit criteria:

- Verification commands run outside the host process.
- Results include command, exit code, stdout, stderr, and environment metadata.
- Failed verification is surfaced clearly.

## Phase 7: Observability And Evaluation

Goal: measure agent quality and improve reliability.

Planned scope:

- Optional LangSmith tracing
- DeepEval-based workflow evaluations
- Test datasets for common FastAPI and Next.js issues
- Metrics for evidence quality, root cause accuracy, and patch success

Exit criteria:

- Agent runs can be inspected.
- Regression tests exist for workflow behavior.
- Quality metrics can be tracked over time.

## Phase 8: Hardening And Expansion

Goal: improve security, extensibility, and framework coverage.

Planned scope:

- Security review of repository handling and patch application
- Expanded framework detectors
- More search providers
- Better monorepo support
- Role-based access controls if multi-user support is added

Exit criteria:

- Threat model is documented.
- The architecture supports additional stacks without rewriting the workflow.
- Production readiness gaps are known and tracked.

