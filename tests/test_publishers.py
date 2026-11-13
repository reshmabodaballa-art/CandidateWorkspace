
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import (
    Base,
    Customer,
    Order,
    OrderHistory,
    IngestionRun,
)

from src.transformation.customer_publisher import publish_customer
from src.transformation.publisher import publish_order


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    with TestSession() as db:
        yield db

    engine.dispose()


def make_customer():
    return {
        "customer_id": "C001",
        "name": "Test Customer",
        "email": "test@example.com",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }


def make_order():
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)

    return {
        "order_id": "O001",
        "customer_id": "C001",
        "amount": Decimal("500.00"),
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }


def setup_order_dependencies(db):
    customer = make_customer()
    db.add(Customer(**customer))

    db.add(
        IngestionRun(
            run_id="run-001",
            status="running",
        )
    )

    db.flush()


def test_customer_rerun_does_not_create_duplicate(db_session):
    customer = make_customer()

    first_result = publish_customer(db_session, customer)
    second_result = publish_customer(db_session, customer)

    db_session.commit()

    count = db_session.scalar(
        select(func.count()).select_from(Customer)
    )

    assert first_result == "inserted"
    assert second_result == "unchanged"
    assert count == 1


def test_order_rerun_does_not_create_duplicate(db_session):
    setup_order_dependencies(db_session)
    order = make_order()

    first_result = publish_order(
        db_session, "run-001", order
    )

    second_result = publish_order(
        db_session, "run-001", order
    )

    db_session.commit()

    count = db_session.scalar(
        select(func.count()).select_from(Order)
    )

    history_count = db_session.scalar(
        select(func.count()).select_from(OrderHistory)
    )

    assert first_result == "inserted"
    assert second_result == "unchanged"
    assert count == 1
    assert history_count == 0


def test_newer_order_version_preserves_previous_history(db_session):
    setup_order_dependencies(db_session)

    original = make_order()

    publish_order(db_session, "run-001", original)

    updated = make_order()
    updated["amount"] = Decimal("750.00")
    updated["status"] = "shipped"
    updated["updated_at"] = (
        original["updated_at"] + timedelta(days=1)
    )

    result = publish_order(
        db_session, "run-001", updated
    )

    db_session.commit()

    saved_order = db_session.get(Order, "O001")

    history = db_session.scalars(
        select(OrderHistory).where(
            OrderHistory.order_id == "O001"
        )
    ).all()

    assert result == "updated"
    assert saved_order.amount == Decimal("750.00")
    assert saved_order.status == "shipped"
    assert len(history) == 1
    assert history[0].record_snapshot["amount"] == "500.00"
    assert history[0].record_snapshot["status"] == "completed"


def test_stale_order_version_is_ignored(db_session):
    setup_order_dependencies(db_session)

    original = make_order()
    publish_order(db_session, "run-001", original)

    stale = make_order()
    stale["amount"] = Decimal("100.00")
    stale["updated_at"] = (
        original["updated_at"] - timedelta(days=1)
    )

    result = publish_order(
        db_session, "run-001", stale
    )

    db_session.commit()

    saved_order = db_session.get(Order, "O001")

    assert result == "stale"
    assert saved_order.amount == Decimal("500.00")


def test_conflicting_order_version_is_rejected(db_session):
    setup_order_dependencies(db_session)

    original = make_order()
    publish_order(db_session, "run-001", original)

    conflicting = make_order()
    conflicting["amount"] = Decimal("900.00")

    with pytest.raises(
        ValueError,
        match="Conflicting order version",
    ):
        publish_order(
            db_session, "run-001", conflicting
        )
