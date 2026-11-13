from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.database.models import RejectedRecord


def quarantine_record(
    db: Session,
    run_id: str,
    endpoint: str,
    record: dict,
    reasons: list[str]
):
    source_record_id = None

    if isinstance(record, dict):
        source_record_id = (
            record.get("order_id")
            or record.get("customer_id")
        )

    rejected = RejectedRecord(
        run_id=run_id,
        endpoint=endpoint,
        source_record_id=(
            str(source_record_id)
            if source_record_id is not None
            else None
        ),
        raw_record=record if isinstance(record, dict) else {
            "raw_value": str(record)
        },
        rejection_reason="; ".join(reasons),
        rejected_at=datetime.now(timezone.utc)
    )

    db.add(rejected)
    return rejected
