
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.database.models import (
    IngestionRun,
    RejectedRecord,
    RawAPIResponse,
)


def get_run_summary(db: Session, run_id: str) -> dict:
    run = db.get(IngestionRun, run_id)

    if run is None:
        raise ValueError(f"Ingestion run not found: {run_id}")

    rejected_count = db.scalar(
        select(func.count())
        .select_from(RejectedRecord)
        .where(RejectedRecord.run_id == run_id)
    )

    raw_response_count = db.scalar(
        select(func.count())
        .select_from(RawAPIResponse)
        .where(RawAPIResponse.run_id == run_id)
    )

    return {
        "run_id": run.run_id,
        "status": run.status,
        "started_at": run.started_at.isoformat(),
        "ended_at": (
            run.ended_at.isoformat() if run.ended_at else None
        ),
        "input_count": run.input_count,
        "output_count": run.output_count,
        "rejected_count": rejected_count or 0,
        "raw_response_count": raw_response_count or 0,
        "error_message": run.error_message,
    }


def get_recent_runs(db: Session, limit: int = 10) -> list:
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    runs = db.scalars(
        select(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "run_id": run.run_id,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "input_count": run.input_count,
            "output_count": run.output_count,
            "rejected_count": run.rejected_count,
        }
        for run in runs
    ]
