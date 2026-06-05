.PHONY: dev backend frontend install test help

# ── Default ──────────────────────────────────────────────
help:
	@echo ""
	@echo "  make dev        Start backend + frontend together"
	@echo "  make backend    Start backend only  (port 8000)"
	@echo "  make frontend   Start frontend only (port 3000)"
	@echo "  make install    Install all dependencies"
	@echo "  make test       Run all tests"
	@echo ""

# ── Dev ──────────────────────────────────────────────────
dev:
	@echo "Starting Agentrail..."
	@trap 'kill 0' EXIT; \
	(cd backend && uv run uvicorn app.main:app --port 8000 --reload) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	cd backend && uv run uvicorn app.main:app --port 8000 --reload

frontend:
	cd frontend && npm run dev

# ── Install ───────────────────────────────────────────────
install:
	@echo "Installing backend deps..."
	cd backend && uv sync --extra dev
	@echo "Installing frontend deps..."
	cd frontend && npm install
	@echo "Done. Copy backend/.env.example to backend/.env and add your API key."

# ── Test ──────────────────────────────────────────────────
test:
	@echo "Running backend tests..."
	cd backend && uv run pytest
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "All checks passed."
