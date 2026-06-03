# Agentrail

**Verification-first AI software engineering agent for evidence-backed bug fixes.**

![Python](https://img.shields.io/badge/Python-3.11+-111111?style=flat&labelColor=0A0A0A)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-111111?style=flat&labelColor=0A0A0A)
![Next.js](https://img.shields.io/badge/Next.js-frontend-111111?style=flat&labelColor=0A0A0A)
![LangGraph](https://img.shields.io/badge/LangGraph-agent_workflow-111111?style=flat&labelColor=0A0A0A)

Agentrail analyzes repositories, finds code evidence, explains root cause, proposes a fix strategy, previews a patch, pauses for human approval, runs tests safely, verifies the result, scores risk, and generates a PR-ready report.

It is a local/portfolio MVP with production-minded safety design. It demonstrates a disciplined engineering loop for AI-assisted debugging without claiming full autonomy or production readiness.

<p align="center">
  <img src="docs/screenshots/dashboard.png" width="32%" alt="Agentrail dashboard" />
  <img src="docs/screenshots/run-detail.png" width="32%" alt="Run detail view" />
  <img src="docs/screenshots/agent-graph.png" width="32%" alt="Agent graph view" />
</p>
<p align="center">
  <img src="docs/screenshots/patch-approval.png" width="48%" alt="Patch approval view" />
  <img src="docs/screenshots/verification-risk.png" width="48%" alt="Verification and risk view" />
</p>

More screenshots and demo notes are available in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## What It Does

| Stage | Output |
| --- | --- |
| Repository scan | Stack, files, test commands |
| Evidence search | Relevant files and line-numbered snippets |
| Root cause | Structured explanation grounded in evidence |
| Fix strategy | High-level plan constrained to evidence |
| Patch preview | Diff preview, not automatic modification |
| Human approval | LangGraph interrupt before verification |
| Test runner | Local safe runner or optional E2B sandbox |
| Verification | Verified, not verified, or manual review |
| Risk scoring | Residual risk with concrete factors |
| PR draft | Copy-ready PR title and Markdown body |

## Core Workflow

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

## Key Features

- Explicit LangGraph workflow with planner, scanner, search, evidence, root-cause, fix-strategy, patch-preview, approval, test, verifier, risk, and reporter nodes.
- Repository scanner for FastAPI, React, Next.js, package files, and candidate test commands.
- Line-numbered evidence records from inspected source, tests, configs, logs, or command output.
- Optional structured LLM root-cause and fix-strategy analysis with deterministic fallback paths.
- Patch-preview-only review loop with persisted approval and rejection states.
- Local allowlisted test runner by default, with optional E2B sandbox execution when configured.
- Run timeline, visual workflow graph, verification panels, risk scoring, final report, and PR draft export.
- Deterministic project-specific eval suite for regression testing the workflow.

## Architecture

```text
Next.js UI
-> FastAPI API
-> LangGraph workflow
-> repo tools / search / evidence
-> optional LLM provider
-> patch preview
-> approval interrupt
-> test runner: local or E2B
-> verifier / risk scorer
-> report / timeline / PR draft
```

Backend: FastAPI, Python, Pydantic v2, SQLAlchemy, LangGraph, SQLite for local development, PostgreSQL-compatible persistence, optional OpenAI structured outputs, and optional E2B sandboxing.

Frontend: Next.js App Router, React, TypeScript, Tailwind CSS, shadcn-style local UI primitives, and React Flow via `@xyflow/react`.

Read the full system design in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Safety Model

Agentrail does not directly modify the original repository. It produces evidence, patch previews, verification results, and PR drafts so a developer can review the change before applying it.

- Patch-preview-only workflow
- Human approval before verification continues
- Command allowlist with `shell=False`
- Secret-file filtering for sandbox uploads
- Optional isolated E2B sandbox runner
- Read-only public GitHub issue and repository import
- Sanitized errors and token handling

Read the detailed safety notes in [docs/SAFETY_MODEL.md](docs/SAFETY_MODEL.md).

## Quickstart

### Backend

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
PYTHONDONTWRITEBYTECODE=1 uv run --isolated --extra dev pytest -p no:cacheprovider

cd frontend
npm run lint
npm run build
```

### Evals

```bash
cd backend
uv run python -m app.evals.runner
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional key for structured LLM root-cause and fix-strategy analysis. |
| `OPENAI_MODEL` | Optional model override for LLM-backed analysis. |
| `LLM_ROOT_CAUSE_ENABLED` | Enables structured LLM root-cause analysis when true. |
| `LLM_FIX_STRATEGY_ENABLED` | Enables structured LLM fix strategy when true. |
| `E2B_ENABLED` | Enables the optional E2B sandbox runner when true. |
| `E2B_API_KEY` | Optional key required only when E2B sandbox execution is enabled. |
| `AGENTRAIL_API_BASE_URL` | Frontend proxy target for the FastAPI backend when deployed separately. |
| `AGENTRAIL_ALLOWED_REPO_ROOTS` | Optional path allowlist for local repository access. |
| `REPO_WORKSPACE_DIR` | Controlled workspace for imported GitHub repositories. |
| `GITHUB_IMPORT_ENABLED` | Enables public GitHub repository import when true. |
| `GITHUB_ISSUE_IMPORT_ENABLED` | Enables read-only public GitHub issue import when true. |
| `GITHUB_API_TIMEOUT_SECONDS` | Timeout for GitHub issue API requests. |
| `GITHUB_TOKEN` | Optional token for GitHub clone access; never required for the public MVP flow. |
| `MAX_ISSUE_BODY_CHARS` | Maximum issue body length copied into run context. |

LLM features, E2B, and GitHub token usage are optional. The local deterministic workflow works without external API keys.

## Demo Flow

1. Create a run from a local repository path, public GitHub repository URL, or public GitHub issue URL.
2. Start the run and watch the event timeline populate.
3. Review the evidence, root cause, and fix strategy.
4. Inspect the patch preview and approve or reject it.
5. Run verification locally or through optional E2B sandboxing.
6. Read the verifier result, residual risk score, final report, and PR draft.

Demo scripts: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Evaluation

Agentrail includes a small deterministic evaluation suite. It is not SWE-bench; it is a project-specific regression suite for validating workflow behavior across controlled fixtures.

Covered scenarios include auth token persistence, missing environment handling, frontend build failure, documentation-only changes, and unsafe command blocking.

```bash
cd backend
uv run python -m app.evals.runner
```

Current documented local output: all five scenarios pass with `100/100`. See [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md).

## Roadmap

Completed MVP work includes the LangGraph workflow, local repository input, public GitHub import, public GitHub issue import, patch previews, approval interrupts, safe verification, risk scoring, final reports, PR draft export, and deterministic evals.

Future work includes real PR creation behind explicit user action, CI integration, durable LangGraph checkpointing, benchmark dashboards, broader framework coverage, and production authentication/authorization.

Read the detailed roadmap in [docs/ROADMAP.md](docs/ROADMAP.md).

## Resume Bullets

- Built a full-stack AI developer tool that helps engineers inspect repositories, gather evidence, preview fixes, approve changes, run tests, and generate final engineering reports.
- Implemented a FastAPI and LangGraph backend with typed workflow state, SQLAlchemy persistence, repository search, approval interrupts, verification, and risk scoring.
- Created a Next.js and TypeScript dashboard for run creation, agent timeline, graph visualization, patch review, test results, risk scoring, and report viewing.

More versions are available in [docs/RESUME_BULLETS.md](docs/RESUME_BULLETS.md).

## GitHub Metadata

Recommended repository description:

```text
Verification-first AI software engineering agent for evidence-backed bug fixes.
```

Recommended topics:

```text
ai-agent
langgraph
fastapi
nextjs
software-engineering
code-review
developer-tools
e2b
github
verification
```

## Documentation

| Document | Purpose |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | System design and LangGraph workflow |
| [Safety Model](docs/SAFETY_MODEL.md) | Approval, sandbox, and command safety |
| [Demo Script](docs/DEMO_SCRIPT.md) | 2-minute and 5-minute demo flow |
| [Evaluation Report](docs/EVAL_REPORT.md) | Project-specific evaluation scenarios |
| [Roadmap](docs/ROADMAP.md) | Completed and future work |
| [Resume Bullets](docs/RESUME_BULLETS.md) | Resume and portfolio-ready summaries |
| [Project Completion](docs/PROJECT_COMPLETION.md) | MVP status, boundaries, and remaining work |
