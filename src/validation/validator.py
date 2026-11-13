from datetime import datetime
from decimal import Decimal, InvalidOperation


VALID_STATUSES = {"pending", "completed", "cancelled"}

REQUIRED_ORDER_FIELDS = {
    "order_id",
    "customer_id",
    "amount",
    "status",
    "created_at",
    "updated_at"
}


def validate_order(record, known_customer_ids, seen_order_ids=None):
    reasons = []

    if not isinstance(record, dict):
        return False, ["Record must be a JSON object"]

    missing_fields = REQUIRED_ORDER_FIELDS - record.keys()

    if missing_fields:
        reasons.append(
            "Missing fields: " + ", ".join(sorted(missing_fields))
        )

    if reasons:
        return False, reasons

    order_id = record["order_id"]
    customer_id = record["customer_id"]

    if not isinstance(order_id, str) or not order_id.strip():
        reasons.append("Invalid order_id")

    if not isinstance(customer_id, str) or not customer_id.strip():
        reasons.append("Invalid customer_id")
    elif customer_id not in known_customer_ids:
        reasons.append("Customer reference does not exist")

    if seen_order_ids is not None and order_id in seen_order_ids:
        reasons.append("Duplicate order_id")

    try:
        amount = Decimal(str(record["amount"]))
        if not amount.is_finite() or amount <= 0:
            reasons.append("Amount must be a positive finite number")
    except (InvalidOperation, ValueError, TypeError):
        reasons.append("Invalid amount")

    if record["status"] not in VALID_STATUSES:
        reasons.append("Invalid order status")

    for field in ("created_at", "updated_at"):
        try:
            parsed = datetime.fromisoformat(
                record[field].replace("Z", "+00:00")
            )
            if parsed.tzinfo is None:
                reasons.append(f"{field} must include a timezone")
        except (ValueError, TypeError, AttributeError):
            reasons.append(f"Invalid {field} timestamp")

    return len(reasons) == 0, reasons
