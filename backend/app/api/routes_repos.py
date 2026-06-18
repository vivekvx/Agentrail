from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.limiter import limiter
from app.db.models import Repo
from app.db.session import get_db
from app.services.repo_map import build_module_graph
from app.services.repo_scanner import (
    RepoUrlError,
    fetch_repo_size_kb,
    parse_github_url,
    scan_repo,
)

router = APIRouter(prefix="/api/repos", tags=["repos"])


class ImportRequest(BaseModel):
    url: str


class RepoSummary(BaseModel):
    id: int
    url: str
    name: str
    status: str
    default_branch: str | None
    file_count: int
    created_at: str


class RepoDetail(RepoSummary):
    languages: list[dict]
    tree: dict | None
    error_message: str | None


def _summary(repo: Repo) -> RepoSummary:
    return RepoSummary(
        id=repo.id,
        url=repo.url,
        name=repo.name,
        status=repo.status,
        default_branch=repo.default_branch,
        file_count=repo.file_count,
        created_at=repo.created_at.isoformat(),
    )


def _detail(repo: Repo) -> RepoDetail:
    return RepoDetail(
        **_summary(repo).model_dump(),
        languages=json.loads(repo.languages_json) if repo.languages_json else [],
        tree=json.loads(repo.tree_json) if repo.tree_json else None,
        error_message=repo.error_message,
    )


@router.post("", response_model=RepoSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().scan_rate_limit)
def import_repo(
    request: Request,
    body: ImportRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RepoSummary:
    settings = get_settings()
    try:
        _, name = parse_github_url(body.url)
        # Pre-flight: verify existence + size before any clone (DoS guard).
        size_kb = fetch_repo_size_kb(name)
    except RepoUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    if size_kb > settings.max_repo_size_kb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Repository too large ({size_kb // 1000} MB); limit is "
            f"{settings.max_repo_size_kb // 1000} MB",
        )

    repo = Repo(url=body.url.strip(), name=name, status="pending")
    db.add(repo)
    db.commit()
    db.refresh(repo)

    background.add_task(scan_repo, repo.id)
    return _summary(repo)


@router.get("", response_model=list[RepoSummary])
def list_repos(limit: int = 20, db: Session = Depends(get_db)) -> list[RepoSummary]:
    rows = db.query(Repo).order_by(desc(Repo.created_at)).limit(limit).all()
    return [_summary(r) for r in rows]


@router.get("/{repo_id}", response_model=RepoDetail)
def get_repo(repo_id: int, db: Session = Depends(get_db)) -> RepoDetail:
    repo = db.get(Repo, repo_id)
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repo not found")
    return _detail(repo)


@router.get("/{repo_id}/map")
def get_repo_map(repo_id: int, db: Session = Depends(get_db)) -> dict:
    repo = db.get(Repo, repo_id)
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repo not found")
    tree = json.loads(repo.tree_json) if repo.tree_json else None
    return build_module_graph(tree)
