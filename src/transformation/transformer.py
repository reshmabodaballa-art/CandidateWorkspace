from datetime import datetime, timezone
from decimal import Decimal


def parse_utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")

    return parsed.astimezone(timezone.utc)


def transform_order(record: dict) -> dict:
    return {
        "order_id": record["order_id"].strip(),
        "customer_id": record["customer_id"].strip(),
        "amount": Decimal(str(record["amount"])).quantize(
            Decimal("0.01")
        ),
        "status": record["status"].strip().lower(),
        "created_at": parse_utc_datetime(record["created_at"]),
        "updated_at": parse_utc_datetime(record["updated_at"])
    }
