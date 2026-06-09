from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import EvalResult as EvalResultModel
from app.evals.metrics import EvalResult as EvalResultMetric
from app.evals.runner import run_eval_scenario
from app.evals.scenarios import EvalScenario, load_default_scenarios

router = APIRouter(prefix="/api/evals", tags=["evals"])


def _scenario_to_db(
    scenario: EvalScenario,
    result: EvalResultMetric,
    db: Session,
) -> EvalResultModel:
    row = EvalResultModel(
        scenario_name=scenario.name,
        score=float(result.score),
        passed=result.passed,
        details_json=json.dumps(
            {
                "scenario_id": result.scenario_id,
                "summary": result.summary,
                "checks": result.checks,
            }
        ),
    )
    db.add(row)
    return row


def _row_to_dict(row: EvalResultModel) -> dict[str, Any]:
    details = None
    if row.details_json:
        try:
            details = json.loads(row.details_json)
        except ValueError:
            details = row.details_json
    return {
        "id": row.id,
        "scenario_name": row.scenario_name,
        "score": row.score,
        "passed": row.passed,
        "details": details,
        "run_at": row.run_at.isoformat() if row.run_at else None,
    }


@router.get("/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    """Return available eval scenario names and IDs."""
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in load_default_scenarios()
    ]


@router.post("/run")
def run_evals(
    scenario_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Trigger eval run(s) and persist results.

    Pass ``scenario_id`` to run a single scenario; omit to run all.
    """
    scenarios = load_default_scenarios()
    if scenario_id is not None:
        scenarios = [s for s in scenarios if s.id == scenario_id]
        if not scenarios:
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    rows: list[EvalResultModel] = []
    for scenario in scenarios:
        result = run_eval_scenario(scenario)
        rows.append(_scenario_to_db(scenario, result, db))

    db.commit()
    for row in rows:
        db.refresh(row)

    return [_row_to_dict(row) for row in rows]


@router.get("/results")
def get_results(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return stored eval results, most recent first."""
    rows = (
        db.query(EvalResultModel)
        .order_by(EvalResultModel.id.desc())
        .limit(limit)
        .all()
    )
    return [_row_to_dict(row) for row in rows]
