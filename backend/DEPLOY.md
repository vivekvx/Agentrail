# Deploying the Agentrail backend

## Environment

Set these (see `.env.example`):

| Var | Notes |
|-----|-------|
| `ENV` | `production` enables strict checks (rejects default `SECRET_KEY`). |
| `SECRET_KEY` | Required in production. `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | SQLite for dev; **Postgres for production** — `postgresql+psycopg://user:pass@host/db`. |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins for CORS. |
| `LOG_LEVEL` | `INFO` (default) / `DEBUG`. |

## Database migrations

Schema is managed by Alembic — `create_all()` is only used by the test suite.
The `Procfile` runs migrations on release:

```
release: uv run --active alembic upgrade head
```

On a host without release phases, run `alembic upgrade head` before starting the
web process. Create new migrations with:

```
uv run alembic revision --autogenerate -m "describe change"
```

## Health checks

- `GET /health` — liveness (process up).
- `GET /ready` — readiness (database reachable); returns 503 if not.

## Scaling constraint (known limitation)

Repo scans run via FastAPI `BackgroundTasks` in the web process, bounded by an
in-process semaphore (`MAX_CONCURRENT_SCANS`). This is correct for a **single
instance** but does not survive horizontal scaling or stateless/serverless
hosts: in-flight scans die with the worker and the semaphore is per-process.

To scale out, move scanning to a real job queue (e.g. `arq`/RQ/Celery + Redis)
with the web process only enqueueing work. The DB layer is already Postgres-ready
(`pool_pre_ping` enabled for server databases), so the remaining work is the
queue, not the storage.
