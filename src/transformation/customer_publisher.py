
from datetime import timezone

from sqlalchemy.orm import Session

from src.database.models import Customer


def to_utc(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def publish_customer(db: Session, record: dict) -> str:

    existing = db.get(Customer, record["customer_id"])

    if existing is None:
        db.add(Customer(**record))
        db.flush()
        return "inserted"

    same_data = (
        existing.name == record["name"]
        and existing.email == record["email"]
        and to_utc(existing.created_at)
        == to_utc(record["created_at"])
    )

    if same_data:
        return "unchanged"

    existing.name = record["name"]
    existing.email = record["email"]
    existing.created_at = record["created_at"]

    db.flush()
    return "updated"
