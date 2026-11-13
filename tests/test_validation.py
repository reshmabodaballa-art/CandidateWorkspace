from src.validation.validator import validate_order


def valid_order():
    return {
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "amount": "250.00",
        "status": "completed",
        "created_at": "2026-11-13T10:00:00+00:00",
        "updated_at": "2026-11-13T10:00:00+00:00"
    }


def test_valid_order():
    valid, reasons = validate_order(valid_order(), {"CUST-001"}, set())
    assert valid is True
    assert reasons == []


def test_unknown_customer():
    valid, reasons = validate_order(valid_order(), {"CUST-002"}, set())
    assert valid is False
    assert "Customer reference does not exist" in reasons


def test_invalid_amount():
    order = valid_order()
    order["amount"] = "-100"
    valid, reasons = validate_order(order, {"CUST-001"}, set())
    assert valid is False
    assert "Amount must be a positive finite number" in reasons


def test_duplicate_order():
    valid, reasons = validate_order(valid_order(), {"CUST-001"}, {"ORD-001"})
    assert valid is False
    assert "Duplicate order_id" in reasons
def test_non_object_record():
    valid, reasons = validate_order(None, {"CUST-001"}, set())
    assert valid is False
    assert "Record must be a JSON object" in reasons


def test_missing_required_field():
    order = valid_order()
    del order["updated_at"]

    valid, reasons = validate_order(order, {"CUST-001"}, set())
    assert valid is False
    assert any("Missing fields" in reason for reason in reasons)