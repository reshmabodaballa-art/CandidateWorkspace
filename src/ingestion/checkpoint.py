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
    next_cursor: str | None,
    run_id: str
):
    checkpoint = Checkpoint(
        endpoint=endpoint,
        next_cursor=next_cursor,
        last_successful_run_id=run_id,
        updated_at=datetime.now(timezone.utc)
    )

    db.merge(checkpoint)

    # Deliberately do not commit here.
    # The caller must commit target data and checkpoint together.
