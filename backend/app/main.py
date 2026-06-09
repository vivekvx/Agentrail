from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_evals import router as evals_router
from app.api.routes_runs import router as runs_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    _warn_missing_llm_key()
    yield


def _warn_missing_llm_key() -> None:
    from app.core.config import get_settings
    import logging

    s = get_settings()
    if (s.llm_root_cause_enabled or s.llm_fix_strategy_enabled) and not (
        s.openai_api_key or ""
    ).strip():
        logging.warning(
            "LLM nodes are enabled (LLM_ROOT_CAUSE_ENABLED / LLM_FIX_STRATEGY_ENABLED) "
            "but OPENAI_API_KEY is not set. LLM analysis will be skipped silently."
        )


app = FastAPI(title="Agentrail API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(evals_router)
app.include_router(runs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "agentrail",
    }
