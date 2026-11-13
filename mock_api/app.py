
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Header, HTTPException, Query

from src.config import settings


app = FastAPI(
    title="YottaFlex Mock API",
    description="Local API for testing paginated data ingestion",
    version="1.0.0"
)


def generate_customers():
    return [
        {
            "customer_id": f"CUST-{i:03d}",
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com",
            "created_at": (
                datetime(2026, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i)
            ).isoformat()
        }
        for i in range(1, 11)
    ]


def generate_orders():
    customers = generate_customers()
    statuses = ["pending", "completed", "cancelled"]

    records = []

    for i in range(1, 101):
        created = (
            datetime(2026, 2, 1, tzinfo=timezone.utc)
            + timedelta(hours=i)
        )

        records.append({
            "order_id": f"ORD-{i:05d}",
            "customer_id": customers[
                (i - 1) % len(customers)
            ]["customer_id"],
            "amount": round(100 + (i * 17.35), 2),
            "status": statuses[(i - 1) % len(statuses)],
            "created_at": created.isoformat(),
            "updated_at": (
                created + timedelta(hours=1)
            ).isoformat()
        })

    return records


def verify_token(authorization):
    expected = f"Bearer {settings.API_TOKEN}"

    if not settings.API_TOKEN or authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token"
        )


def filter_updated_records(records, timestamp_field, updated_since):
    """Return records updated or created at/after the watermark."""

    if updated_since is None:
        return records

    if updated_since.tzinfo is None:
        updated_since = updated_since.replace(
            tzinfo=timezone.utc
        )
    else:
        updated_since = updated_since.astimezone(timezone.utc)

    filtered = []

    for record in records:
        record_timestamp = datetime.fromisoformat(
            record[timestamp_field].replace("Z", "+00:00")
        )

        if record_timestamp >= updated_since:
            filtered.append(record)

    return filtered


def paginate(records, cursor, page_size):
    try:
        offset = int(cursor) if cursor is not None else 0
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor"
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor"
        )

    page = records[offset:offset + page_size]
    next_offset = offset + len(page)

    return {
        "data": page,
        "next_cursor": (
            str(next_offset)
            if next_offset < len(records)
            else None
        ),
        "total": len(records)
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "YottaFlex Mock API"
    }


@app.get("/mock-api/customers")
def get_customers(
    cursor: str | None = None,
    page_size: int = Query(default=10, ge=1, le=1000),
    updated_since: datetime | None = None,
    authorization: str | None = Header(default=None)
):
    verify_token(authorization)

    records = filter_updated_records(
        generate_customers(),
        "created_at",
        updated_since
    )

    return paginate(records, cursor, page_size)


@app.get("/mock-api/orders")
def get_orders(
    cursor: str | None = None,
    page_size: int = Query(default=10, ge=1, le=1000),
    updated_since: datetime | None = None,
    authorization: str | None = Header(default=None)
):
    verify_token(authorization)

    records = filter_updated_records(
        generate_orders(),
        "updated_at",
        updated_since
    )

    return paginate(records, cursor, page_size)


# One-time failure simulation for retry testing
_simulated_failures = set()


@app.get("/mock-api/test/failure")
def test_transient_failure(
    failure_type: str = Query(default="503"),
    authorization: str | None = Header(default=None)
):
    verify_token(authorization)

    if failure_type not in {"429", "503"}:
        raise HTTPException(
            status_code=400,
            detail="Use 429 or 503"
        )

    if failure_type not in _simulated_failures:
        _simulated_failures.add(failure_type)

        if failure_type == "429":
            raise HTTPException(
                status_code=429,
                detail="Simulated rate limit. Retry after one second.",
                headers={"Retry-After": "1"}
            )

        raise HTTPException(
            status_code=503,
            detail="Simulated temporary server failure"
        )

    return {
        "status": "success",
        "message": f"Temporary {failure_type} failure recovered",
        "failure_type": failure_type
    }
