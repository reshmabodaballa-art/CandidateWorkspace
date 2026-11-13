from sqlalchemy.orm import Session
from src.database.models import Customer


def publish_customer(db: Session, record: dict) -> str:
    existing = db.get(Customer, record["customer_id"])

    if existing is None:
        db.add(Customer(**record))
        db.flush()
        return "inserted"

    existing.name = record["name"]
    existing.email = record["email"]
    existing.created_at = record["created_at"]

    db.flush()
    return "updated"
