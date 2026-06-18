from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.routes_auth import router as auth_router
from app.api.routes_repos import router as repos_router
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.observability import RequestLoggingMiddleware, configure_logging
from app.db.session import SessionLocal, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    yield


settings = get_settings()

app = FastAPI(title="Agentrail API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(repos_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok", "service": "agentrail"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness: the process can reach its database."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    finally:
        db.close()
    return {"status": "ready"}
