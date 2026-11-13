
import pytest
import requests

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import (
    Base,
    Checkpoint,
    IngestionRun,
)
from src.ingestion import pipeline


@pytest.fixture
def test_db(monkeypatch):
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

    monkeypatch.setattr(pipeline, "SessionLocal", TestSession)

    yield TestSession

    engine.dispose()


def test_pipeline_resumes_after_api_failure(test_db, monkeypatch):
    requested_cursors = []

    class FakeClient:
        def close(self):
            pass

    monkeypatch.setattr(
        pipeline,
        "APIClient",
        FakeClient,
    )

    def fake_iter_pages(client, endpoint, start_cursor=None):
        requested_cursors.append(start_cursor)

        if len(requested_cursors) == 1:
            yield {
                "endpoint": endpoint,
                "page_number": 1,
                "request_cursor": None,
                "next_cursor": "10",
                "records": [],
                "raw_response": {
                    "data": [],
                    "next_cursor": "10",
                },
            }

            raise requests.ConnectionError(
                "Simulated API connection failure"
            )

        yield {
            "endpoint": endpoint,
            "page_number": 2,
            "request_cursor": "10",
            "next_cursor": None,
            "records": [],
            "raw_response": {
                "data": [],
                "next_cursor": None,
            },
        }

    monkeypatch.setattr(
        pipeline,
        "iter_pages",
        fake_iter_pages,
    )

    # First run: page one succeeds, then the API fails.
    with pytest.raises(requests.ConnectionError):
        pipeline.run_ingestion("orders")

    # Second run: it should resume from cursor "10".
    result = pipeline.run_ingestion("orders")

    assert requested_cursors == [None, "10"]
    assert result["status"] == "completed"
    assert result["input_count"] == 0

    with test_db() as db:
        checkpoint = db.get(Checkpoint, "orders")

        assert checkpoint is not None
        assert checkpoint.next_cursor is None
        assert checkpoint.last_successful_run_id == result["run_id"]

        runs = db.scalars(
            select(IngestionRun).order_by(
                IngestionRun.started_at
            )
        ).all()

        assert len(runs) == 2
        assert runs[0].status == "failed"
        assert runs[1].status == "completed"

def test_finalization_failure_preserves_previous_checkpoint(
    test_db,
    monkeypatch
):
    # Create a previously committed checkpoint.
    with test_db() as db:
        db.add(
            Checkpoint(
                endpoint="orders",
                next_cursor="10",
            )
        )
        db.commit()

    class FakeClient:
        def close(self):
            pass

    monkeypatch.setattr(
        pipeline,
        "APIClient",
        FakeClient,
    )

    # Simulate the final page.
    def fake_iter_pages(client, endpoint, start_cursor=None):
        assert start_cursor == "10"

        yield {
            "endpoint": endpoint,
            "page_number": 2,
            "request_cursor": "10",
            "next_cursor": None,
            "records": [],
            "raw_response": {
                "data": [],
                "next_cursor": None,
            },
        }

    monkeypatch.setattr(
        pipeline,
        "iter_pages",
        fake_iter_pages,
    )

    # Complete checkpoint update, then simulate a failure
    # before the transaction can commit.
    original_mark_completed = pipeline.mark_checkpoint_completed

    def fail_after_checkpoint_update(db, endpoint, run_id):
        original_mark_completed(db, endpoint, run_id)
        raise RuntimeError("Simulated finalization failure")

    monkeypatch.setattr(
        pipeline,
        "mark_checkpoint_completed",
        fail_after_checkpoint_update,
    )

    with pytest.raises(RuntimeError, match="finalization failure"):
        pipeline.run_ingestion("orders")

    # The rollback must preserve the previous cursor.
    with test_db() as db:
        checkpoint = db.get(Checkpoint, "orders")

        assert checkpoint.next_cursor == "10"
        assert checkpoint.last_successful_run_id is None

        runs = db.scalars(
            select(IngestionRun)
        ).all()

        assert len(runs) == 1
        assert runs[0].status == "failed"
