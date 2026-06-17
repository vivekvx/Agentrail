from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import Repo
from app.db.session import get_db
from app.services.repo_scanner import RepoUrlError, parse_github_url, scan_repo

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
def import_repo(
    body: ImportRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RepoSummary:
    try:
        _, name = parse_github_url(body.url)
    except RepoUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

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
