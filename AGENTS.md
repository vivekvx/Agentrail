# AGENTS.md

## Project
Agentrail is a verification-first AI coding agent.

## Tech Stack
Backend: FastAPI, Python, Pydantic v2, SQLAlchemy, PostgreSQL.
Frontend: Next.js, TypeScript, Tailwind, shadcn/ui.
Agent: LangGraph.
Search: ripgrep first, Probe later.
Sandbox: local safe runner first, E2B later.

## Build Rules
- Work phase by phase.
- Do not implement future phases unless asked.
- Prefer small, testable modules.
- Use type hints.
- Add error handling.
- Do not hardcode secrets.
- Do not run unsafe commands.
- Never modify user repositories directly.
- Generate patch diffs first.

## Commands
Backend:
- cd backend
- python -m pytest

Frontend:
- cd frontend
- npm run lint
- npm run build

## Safety
- Mask .env values.
- Block dangerous shell commands.
- Keep all repo actions scoped to selected repo path.
- Require approval before applying patches.
