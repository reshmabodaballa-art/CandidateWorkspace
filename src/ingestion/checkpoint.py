
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Checkpoint


def get_checkpoint(db: Session, endpoint: str):
    statement = select(Checkpoint).where(
        Checkpoint.endpoint == endpoint
    )
    return db.execute(statement).scalar_one_or_none()


def save_checkpoint(
    db: Session,
    endpoint: str,
    next_cursor: str | None
):
    checkpoint = get_checkpoint(db, endpoint)

    if checkpoint is None:
        checkpoint = Checkpoint(endpoint=endpoint)
        db.add(checkpoint)
        db.flush()

    checkpoint.next_cursor = next_cursor
    checkpoint.updated_at = datetime.now(timezone.utc)


def mark_checkpoint_completed(
    db: Session,
    endpoint: str,
    run_id: str,
    watermark: datetime | None = None
):
    checkpoint = get_checkpoint(db, endpoint)

    if checkpoint is None:
        checkpoint = Checkpoint(endpoint=endpoint)
        db.add(checkpoint)
        db.flush()

    checkpoint.next_cursor = None
    checkpoint.last_successful_run_id = run_id

    if watermark is not None:
        checkpoint.last_successful_watermark = watermark

    checkpoint.updated_at = datetime.now(timezone.utc)
