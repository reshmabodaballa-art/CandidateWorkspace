from datetime import datetime, timezone


def transform_customer(record: dict) -> dict:
    customer_id = record["customer_id"].strip()
    name = record["name"].strip()
    email = record["email"].strip().lower()

    if not customer_id:
        raise ValueError("Customer ID cannot be empty")

    if not name:
        raise ValueError("Customer name cannot be empty")

    if not email or "@" not in email:
        raise ValueError("Invalid customer email")

    created_at = datetime.fromisoformat(
        record["created_at"].replace("Z", "+00:00")
    )

    if created_at.tzinfo is None:
        raise ValueError("Customer timestamp must include a timezone")

    return {
        "customer_id": customer_id,
        "name": name,
        "email": email,
        "created_at": created_at.astimezone(timezone.utc)
    }
