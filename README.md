# Agentrail

**Verification-first AI agent for evidence-backed bug fixes.**

![Python](https://img.shields.io/badge/Python-3.11+-111111?style=flat&labelColor=0A0A0A)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-111111?style=flat&labelColor=0A0A0A)
![Next.js](https://img.shields.io/badge/Next.js-frontend-111111?style=flat&labelColor=0A0A0A)
![LangGraph](https://img.shields.io/badge/LangGraph-agent_workflow-111111?style=flat&labelColor=0A0A0A)

Agentrail scans a repository, collects code evidence, explains root cause, proposes a fix strategy, previews a patch, pauses for human approval, runs tests, scores risk, and exports a PR-ready report — without writing to your repository.

> Local/portfolio MVP with production-minded safety design. Not a fully autonomous coding system.

<p align="center">
  <img src="docs/screenshots/hero-dashboard.png" width="32%" alt="Agentrail command center" />
  <img src="docs/screenshots/agent-graph.png" width="32%" alt="Agent workflow pipeline" />
  <img src="docs/screenshots/verification-risk.png" width="32%" alt="Safety model boundaries" />
</p>

---

## Pipeline

| Stage | Output |
|---|---|
| Scan | Detected stack, key files, test commands |
| Search | Relevant files with line-numbered matches |
| Evidence | Code snippets grounded in source |
| Root cause | Structured explanation backed by evidence |
| Fix strategy | High-level change plan constrained to evidence |
| Patch preview | Unified diff — no automatic file writes |
| **Approval gate** | **LangGraph interrupt — you decide** |
| Test runner | Allowlisted local runner or optional E2B sandbox |
| Verification | Verified / not verified / needs manual review |
| Risk scoring | Residual risk with concrete factors |
| PR draft | Copy-ready title and Markdown body |

---

## Quickstart

**Requirements:** Python 3.11+, Node.js 18+, [uv](https://github.com/astral-sh/uv)

### 1. Backend

```bash
cd backend
cp .env.example .env   # add your API key (see Configuration)
uv sync --extra dev
uv run uvicorn app.main:app --port 8000 --reload
```

> **Database:** The default `DATABASE_URL` points to Postgres. For local dev without Postgres, set `DATABASE_URL=sqlite:///./agentrail.db` in `backend/.env`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Create a run

1. Enter a local **Repo Path** (e.g. `/path/to/your-project`)
2. Describe the bug in **User Task**
3. Set a **Test Command** (e.g. `python -m pytest`)
4. Click **Create Run** → **Start Run**
5. Review the patch diff → **Approve** or **Reject**

---

## Configuration

Copy `backend/.env.example` to `backend/.env`. All external integrations are optional — the deterministic workflow runs without any API keys.

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | LLM provider key (OpenAI or any OpenAI-compatible endpoint) |
| `OPENAI_BASE_URL` | Override endpoint — use `https://api.groq.com/openai/v1` for Groq |
| `OPENAI_MODEL` | Model name, e.g. `llama-3.3-70b-versatile` |
| `LLM_ROOT_CAUSE_ENABLED` | Enable LLM root-cause analysis (`true`/`false`) |
| `LLM_FIX_STRATEGY_ENABLED` | Enable LLM fix-strategy generation (`true`/`false`) |
| `GITHUB_TOKEN` | GitHub PAT for private repo access (optional) |
| `GITHUB_IMPORT_ENABLED` | Allow public repo cloning (`true`/`false`) |
| `E2B_ENABLED` | Use E2B cloud sandbox for test execution (`true`/`false`) |
| `E2B_API_KEY` | E2B API key |
| `AGENTRAIL_ALLOWED_REPO_ROOTS` | Comma-separated local paths the agent may access |

**Free LLM option:** sign up at [console.groq.com](https://console.groq.com) (no credit card required), then set:

```env
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_...
OPENAI_MODEL=llama-3.3-70b-versatile
LLM_ROOT_CAUSE_ENABLED=true
LLM_FIX_STRATEGY_ENABLED=true
```

---

## Safety

Nothing happens to your repository without your explicit action.

- **Patch-preview only** — diffs are displayed, never applied automatically
- **Human approval gate** — LangGraph interrupts the pipeline; you approve or reject
- **Command allowlist** — test runner uses `shell=False` and an explicit allowlist
- **Secret-file filtering** — `.env`, key files, and credential patterns are excluded
- **Read-only GitHub import** — no write tokens used during repo or issue import
- **Sanitized errors** — raw tracebacks and tokens are scrubbed before display

See [docs/SAFETY_MODEL.md](docs/SAFETY_MODEL.md) for full details.

---

## One-Command Dev

```bash
make install   # install all deps (first time only)
make dev       # start backend (8000) + frontend (3000) together
```

Other targets:

```bash
make backend   # backend only
make frontend  # frontend only
make test      # run all tests + frontend build check
```

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
```

Set environment variable in Vercel dashboard:

```
AGENTRAIL_API_BASE_URL = https://your-backend.railway.app/api
```

### Backend → Railway (free tier)

1. Install Railway CLI: `npm install -g @railway/cli`
2. `railway login`
3. `cd backend && railway up`
4. Set env vars in Railway dashboard (same as `backend/.env`)

> **Note:** The backend requires persistent storage and long-running processes — it cannot run on Vercel. Use Railway, Render, or Fly.io instead.

---

## Tests

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
npm run build
npm run lint
```

## Evaluation

Agentrail ships a deterministic regression suite — project-specific fixtures that validate workflow behavior end-to-end.

```bash
cd backend
uv run python -m app.evals.runner
```

All five scenarios currently pass at `100/100`. See [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md).

---

## Roadmap

**Shipped:** LangGraph workflow, local and GitHub repo input, GitHub issue import, patch previews, approval gate, safe test runner, risk scoring, PR draft export, run history, diff highlighting, deterministic evals.

**Planned:** real GitHub PR creation, CI integration, durable checkpointing, benchmark dashboard, broader framework coverage, production auth.

See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design and LangGraph workflow |
| [Safety Model](docs/SAFETY_MODEL.md) | Approval, sandbox, and command safety |
| [Demo Script](docs/DEMO_SCRIPT.md) | 2-minute and 5-minute demo walkthrough |
| [Evaluation Report](docs/EVAL_REPORT.md) | Evaluation scenarios and results |
| [Roadmap](docs/ROADMAP.md) | Completed and planned work |
