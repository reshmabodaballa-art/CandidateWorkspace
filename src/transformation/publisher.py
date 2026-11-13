from datetime import timezone

from sqlalchemy.orm import Session

from src.database.models import Customer, Order, OrderHistory


def to_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def order_snapshot(order):
    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "amount": str(order.amount),
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat()
    }


def publish_order(db: Session, run_id: str, record: dict) -> str:
    """
    Insert a new order or safely update an existing order.

    The caller controls the transaction and commits the order
    together with the corresponding checkpoint.
    """

    customer = db.get(Customer, record["customer_id"])

    if customer is None:
        raise ValueError(
            f"Unknown customer reference: {record['customer_id']}"
        )

    existing = db.get(Order, record["order_id"])

    if existing is None:
        db.add(Order(**record))
        db.flush()
        return "inserted"

    incoming_time = to_utc(record["updated_at"])
    existing_time = to_utc(existing.updated_at)

    if incoming_time < existing_time:
        return "stale"

    if incoming_time == existing_time:
        same_data = (
            existing.customer_id == record["customer_id"]
            and existing.amount == record["amount"]
            and existing.status == record["status"]
        )

        if same_data:
            return "unchanged"

        raise ValueError(
            f"Conflicting order version with identical timestamp: "
            f"{record['order_id']}"
        )

    # Preserve the previous version before updating.
    db.add(
        OrderHistory(
            order_id=existing.order_id,
            run_id=run_id,
            record_snapshot=order_snapshot(existing)
        )
    )

    existing.customer_id = record["customer_id"]
    existing.amount = record["amount"]
    existing.status = record["status"]
    existing.updated_at = record["updated_at"]

    db.flush()
    return "updated"
