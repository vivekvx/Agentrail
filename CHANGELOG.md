# Changelog

## [Unreleased]

### Added
- Postgres support with Alembic migrations (SQLite kept as fallback for local dev)
- JWT authentication — register/login endpoints, per-user run isolation
- SSE streaming for live run event updates (replaces 5-second polling)
- GitHub PR creation from run PR drafts
- Eval runner API and dashboard
- GitHub Actions CI for backend tests and frontend build
- Docker Compose for one-command local start

### Fixed
- CORS middleware added for frontend-backend communication
- FK cascade delete on run_events when agent_run deleted

### Changed
- Default database changed to PostgreSQL
