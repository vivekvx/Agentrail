from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Postgres (or other server DBs): validate connections before use so a
    # dropped/stale connection from the pool doesn't surface as a 500.
    return {"pool_pre_ping": True, "pool_recycle": 1800}


def _enable_sqlite_concurrency(dbapi_connection, _record) -> None:
    # WAL allows concurrent readers during a write; busy_timeout makes
    # writers wait for the lock instead of failing with "database is locked".
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))

if settings.database_url.startswith("sqlite"):
    event.listen(engine, "connect", _enable_sqlite_concurrency)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
