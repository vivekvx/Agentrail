# Agentrail — Product Requirements Document

## Vision

Agentrail is a **codebase onboarding agent**. Point it at any repository and it maps the codebase, generates a guided interactive tour, produces living documentation, and lets engineers ask questions — tracking understanding over time.

**Name rationale:** Agent + Trail = a guided trail through code.

---

## Problem

Onboarding to a new codebase is slow, painful, and inconsistent. Engineers spend 2-4 weeks reading scattered READMEs, grepping code, and interrupting senior devs. Knowledge lives in people's heads, not in the system.

## Target Users

- **New hires** joining a team with an existing codebase
- **Team leads** who want consistent onboarding without manual walkthroughs
- **Solo devs / OSS maintainers** who want their repo to be self-documenting
- **IC engineers** context-switching between projects

## Core User Journey

1. **Connect** — paste a GitHub URL or point to a local repo
2. **Scan** — agent crawls the codebase: file tree, dependencies, entry points, architecture patterns, key abstractions
3. **Map** — generates an interactive codebase graph (architecture diagram, module relationships, data flow)
4. **Tour** — produces a guided walkthrough: "start here, then this, then that" with contextual explanations
5. **Ask** — interactive Q&A grounded in the actual code ("where is auth handled?", "how does data flow from API to DB?")
6. **Track** — dashboard showing onboarding progress, areas explored vs unexplored, confidence scores

---

## Features (MVP — v0.1)

### F1: Repo Import
- GitHub URL input (public repos first, private via OAuth later)
- Clone + index in background
- Show progress during scan

### F2: Codebase Scanner
- Language/framework detection
- Dependency graph extraction (package.json, pyproject.toml, go.mod, Cargo.toml, etc.)
- Entry point identification (main files, API routes, CLI commands)
- Architecture pattern recognition (MVC, microservices, monorepo, etc.)

### F3: Interactive Codebase Map
- Visual graph of modules/packages and their relationships (React Flow)
- Click-to-explore: select a node → see files, exports, key functions
- Color-coded by module type (API, DB, UI, utils, tests)
- Zoom levels: high-level architecture → package → file → function

### F4: Guided Tour Generator
- LLM-generated narrative walkthrough of the codebase
- Ordered sequence: "start with X because it's the entry point, then Y handles routing..."
- Each step links to actual files/lines
- Contextual explanations: why this pattern, what this abstraction does

### F5: Code Q&A (Chat)
- Ask questions about the codebase in natural language
- Answers grounded in actual code with file references
- RAG over indexed codebase (embeddings + code search)
- Conversation history per repo

### F6: Onboarding Dashboard
- Progress tracker: modules explored, tour completion
- "Areas you haven't looked at yet" suggestions
- Time-on-codebase metrics
- Per-user state (each engineer has their own onboarding trail)

---

## Features (v0.2 — Post-MVP)

- Private repo support (GitHub OAuth)
- Team admin: assign repos, track team onboarding progress
- Auto-update: re-scan on new commits, highlight what changed
- Custom tour authoring: leads can annotate the auto-generated tour
- Slack/Discord bot: ask codebase questions from chat
- Multi-repo support per workspace
- Export tour as Markdown/Notion

---

## Tech Stack

### Backend — **FastAPI + Python**
- Already have: JWT auth, rate limiting, SSE streaming, SQLite/Postgres
- Add: LangGraph for agent orchestration, tree-sitter for code parsing, embeddings for RAG
- LLM: Claude API (primary), OpenAI fallback

### Frontend — **Next.js 14 + React**
- Already have: WebGL backdrop, GSAP motion, React Flow, auth pages, dark theme
- Add: chat interface, tour viewer, progress dashboard
- Keep: Geist font, dark canvas aesthetic, shadcn/ui primitives

### Infra
- SQLite for dev, Postgres for prod
- Vector store: pgvector or ChromaDB for code embeddings
- File storage: local clone → indexed chunks

---

## Design Direction

### Keep from current
- Dark canvas (#0a0a0a), hairline borders, no shadows
- WebGL ambient backdrop
- GSAP motion (subtle, purposeful)
- Geist Sans + Mono typography
- Engineered, restrained aesthetic

### New surfaces
- **Codebase map** — React Flow graph, primary hero surface. Color-coded nodes, clean edges, interactive zoom.
- **Tour viewer** — left: step navigation, right: code panel with highlighted lines. Reading-focused, mono font for code.
- **Chat** — minimal, right-rail or full-page. Code blocks rendered with syntax highlighting.
- **Dashboard** — progress rings/bars, module coverage grid, clean data viz.

### Brand personality update
Engineered, calm, trustworthy — now also **guiding** and **explorable**. A well-lit trail through a forest, not a lab instrument.

---

## Data Model (new)

### Repo
- id, url, name, default_branch, last_scanned_at, scan_status, owner_id

### CodeModule
- id, repo_id, name, path, module_type (api/db/ui/util/test), description, parent_module_id

### CodeFile
- id, module_id, path, language, summary, embedding_vector

### Tour
- id, repo_id, title, generated_at, steps (JSON or relation)

### TourStep
- id, tour_id, order, title, explanation, file_path, line_start, line_end

### ChatMessage
- id, repo_id, user_id, role (user/assistant), content, file_refs (JSON), created_at

### OnboardingProgress
- id, user_id, repo_id, modules_visited (JSON), tour_steps_completed, last_active_at

---

## API Endpoints (planned)

```
POST   /api/repos                  — import a repo
GET    /api/repos/:id              — repo details + scan status
GET    /api/repos/:id/map          — codebase graph data
GET    /api/repos/:id/tour         — generated tour
POST   /api/repos/:id/chat         — ask a question (SSE stream)
GET    /api/repos/:id/progress     — user's onboarding progress
PATCH  /api/repos/:id/progress     — update progress
```

Auth endpoints (existing): `/api/auth/register`, `/api/auth/login`, `/api/auth/me`

---

## Success Metrics

- Time-to-first-question < 2 min after repo import
- Tour covers ≥80% of key modules
- Users complete tour within 1 session
- Chat answers cite correct files ≥90% of time
- NPS > 50 among onboarding engineers

---

## Non-Goals (MVP)

- Code editing or generation
- CI/CD integration
- Code review
- Bug detection or fixing
- Multi-language support in same repo (pick dominant language)
