# Agentrail

**Onboard to any codebase in minutes, not weeks.**

![Python](https://img.shields.io/badge/Python-3.11+-111111?style=flat&labelColor=0A0A0A)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-111111?style=flat&labelColor=0A0A0A)
![Next.js](https://img.shields.io/badge/Next.js-frontend-111111?style=flat&labelColor=0A0A0A)
![Ollama](https://img.shields.io/badge/Ollama-local_LLM-111111?style=flat&labelColor=0A0A0A)
![CI](https://github.com/vivekvx/Agentrail/actions/workflows/ci.yml/badge.svg)

Agentrail is a codebase onboarding agent. Point it at a public GitHub repository and it clones the code, maps the architecture, generates a guided tour, and answers questions — all grounded in the actual source. The AI runs locally on [Ollama](https://ollama.com), so there is no API cost and no vector database to operate.

> The walkthrough a senior engineer would give a new hire — generated automatically, per repository.

---

## What it does

Paste a GitHub URL → Agentrail scans the repo, then gives you five ways to explore it:

| View | What it shows |
|---|---|
| **Map** | Interactive module graph (React Flow) derived from the file tree — nodes sized by file count, colored by dominant language |
| **Tour** | An ordered, LLM-generated walkthrough: where to start and why, with file references |
| **Chat** | Code Q&A over the repo (local RAG) — every answer cites the source files it used |
| **Docs** | Living documentation composed from the map + tour, downloadable as Markdown |
| **Tree** | Collapsible file tree with per-file language detection |

---

## How it works

```
GitHub URL ──▶ shallow clone ──▶ walk tree + detect stack ──▶ embed files (Ollama)
                                          │
        ┌─────────────────┬──────────────┼──────────────┬─────────────────┐
       Map              Tour            Chat            Docs              Tree
   module graph     LLM walkthrough   RAG Q&A       Markdown export    file tree
```

- **Scan** is a depth-1 git clone; the working copy is deleted after indexing.
- **RAG** chunks text files, embeds them with `nomic-embed-text`, and retrieves the top matches by cosine similarity in-process — brute force is plenty at single-repo scale, so there is no external vector store.
- **Map / Tree / Docs** work without an LLM; **Tour** and **Chat** need Ollama running.

---

## Quickstart

**Requirements:** Python 3.11+, Node.js 18+, [uv](https://github.com/astral-sh/uv), and [Ollama](https://ollama.com) (optional — only for Tour and Chat).

### 1. Ollama (optional, for AI features)

```bash
ollama pull llama3.2          # tour + chat generation
ollama pull nomic-embed-text  # embeddings for chat
```

### 2. Backend

```bash
cd backend
cp .env.example .env
uv sync --extra dev
uv run uvicorn app.main:app --port 8000 --reload
```

Defaults to SQLite — no database to install.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000), paste a public GitHub URL, and explore.

---

## Configuration

Copy `backend/.env.example` to `backend/.env`. Everything has a working default.

| Variable | Purpose | Default |
|---|---|---|
| `ENV` | `production` enforces a real `SECRET_KEY` | `development` |
| `DATABASE_URL` | SQLite for dev, Postgres for production | `sqlite:///./agentrail.db` |
| `SECRET_KEY` | Auth signing key — **required in production** | dev placeholder |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `OLLAMA_BASE_URL` | Ollama endpoint for tour + chat | `http://localhost:11434` |
| `OLLAMA_MODEL` | Generation model | `llama3.2` |
| `OLLAMA_EMBED_MODEL` | Embedding model | `nomic-embed-text` |

Repo-scan and RAG limits (`MAX_REPO_SIZE_KB`, `MAX_CONCURRENT_SCANS`, `RAG_MAX_CHUNKS`, …) are also configurable — see `app/core/config.py`.

---

## Tech stack

- **Backend** — Python, FastAPI, SQLAlchemy, Alembic migrations, SQLite → Postgres.
- **Frontend** — Next.js (App Router), React 19, TypeScript, Tailwind v4, React Flow, GSAP. Dual dark/light theme.
- **AI** — local-first via Ollama; in-process cosine RAG (no paid API, no vector DB).
- **Infra** — Dockerized backend, GitHub Actions CI (lint, type-check, tests, dependency audit), Vercel + Render/Neon deployment.

---

## Security & hardening

The repo-import endpoint is public, so it is hardened against abuse:

- **Rate limiting** — per-IP cap on imports (slowapi).
- **Size pre-flight** — repo size checked via the GitHub API before any clone; oversized or missing repos are rejected.
- **Bounded concurrency** — a semaphore caps simultaneous clones.
- **Hardened proxy** — the frontend API proxy only forwards to allowlisted backend paths.
- **Security headers** — CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`.
- **Secret enforcement** — startup fails in production if `SECRET_KEY` is the default.
- **Error sanitization** — raw git/internal errors are logged server-side, never returned to clients.

---

## Tests & CI

```bash
cd backend && uv run pytest        # 47 tests
cd backend && uv run ruff check .  # lint
cd frontend && npm run build       # type-check + build
cd frontend && npx eslint .        # lint
```

CI runs all of the above plus formatting and dependency audits on every push.

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
```

Set `AGENTRAIL_API_BASE_URL = https://your-backend.onrender.com/api` in the Vercel dashboard.

### Backend → Render + Neon (free tiers)

1. Create a Postgres database on [Neon](https://neon.tech) and copy the connection string.
2. On [Render](https://render.com): New → Web Service → connect this repo, root `backend`, runtime Docker.
3. Set env vars: `ENV=production`, `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`), `DATABASE_URL` (Neon), `ALLOWED_ORIGINS` (your Vercel URL).

The Docker image installs `git`, runs Alembic migrations on boot, and binds to the host `$PORT`. See [backend/DEPLOY.md](backend/DEPLOY.md) for details and the known single-instance scan constraint.

> **Note on AI features when hosted:** Tour and Chat need an LLM the *server* can reach. A typical free host can't run Ollama, so point `OLLAMA_BASE_URL` at a hosted OpenAI-compatible endpoint — or run the backend locally for the full experience. Map, Tree, and Docs work everywhere.

---

## Project layout

```
backend/
  app/
    api/        FastAPI routes (auth, repos, map, tour, chat)
    core/       config, security, rate limiting, observability
    db/         models, session
    services/   repo_scanner, repo_map, tour, rag
  alembic/      migrations
  tests/        pytest suite
frontend/
  src/app/        routes (home, explore, repo/[id])
  src/components/ map, tour, chat, docs, site chrome, theme toggle
  src/lib/        api client, motion helpers
```

---

## Status

Working: import · scan · map · tour · chat · docs · tree, with migrations, CI, and 47 tests.

Roadmap: hosted backend + cloud LLM fallback so AI features work for every visitor; per-user progress tracking; multi-repo workspaces.
