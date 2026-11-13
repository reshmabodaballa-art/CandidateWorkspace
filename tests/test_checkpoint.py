
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base, Checkpoint
from src.ingestion.checkpoint import (
    get_checkpoint,
    save_checkpoint,
    mark_checkpoint_completed,
)


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

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_save_checkpoint_stores_next_cursor(db_session):
    save_checkpoint(
        db_session,
        "orders",
        "20"
    )
    db_session.commit()

    checkpoint = get_checkpoint(db_session, "orders")

    assert checkpoint is not None
    assert checkpoint.next_cursor == "20"
    assert checkpoint.last_successful_run_id is None


def test_checkpoint_can_be_resumed_after_session_restart(db_session):
    save_checkpoint(
        db_session,
        "orders",
        "30"
    )
    db_session.commit()

    db_session.close()

    # Open a new session against the same test database.
    engine = db_session.get_bind()
    TestSession = sessionmaker(bind=engine)

    with TestSession() as new_db:
        checkpoint = get_checkpoint(new_db, "orders")

        assert checkpoint is not None
        assert checkpoint.next_cursor == "30"


def test_completed_checkpoint_records_successful_run(db_session):
    save_checkpoint(
        db_session,
        "customers",
        "10"
    )

    mark_checkpoint_completed(
        db_session,
        "customers",
        "run-123"
    )
    db_session.commit()

    checkpoint = get_checkpoint(db_session, "customers")

    assert checkpoint.next_cursor is None
    assert checkpoint.last_successful_run_id == "run-123"


def test_existing_checkpoint_is_updated_not_duplicated(db_session):
    save_checkpoint(
        db_session,
        "orders",
        "10"
    )
    db_session.commit()

    save_checkpoint(
        db_session,
        "orders",
        "20"
    )
    db_session.commit()

    checkpoints = db_session.query(Checkpoint).filter_by(
        endpoint="orders"
    ).all()

    assert len(checkpoints) == 1
    assert checkpoints[0].next_cursor == "20"
