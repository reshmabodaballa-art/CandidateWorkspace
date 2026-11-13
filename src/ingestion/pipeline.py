
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from src.database.connection import SessionLocal
from src.database.models import (
    Customer,
    IngestionRun,
    RawAPIResponse,
)

from src.ingestion.api_client import APIClient
from src.ingestion.paginator import iter_pages
from src.ingestion.checkpoint import (
    get_checkpoint,
    save_checkpoint,
    mark_checkpoint_completed,
)

from src.transformation.customer_transformer import transform_customer
from src.transformation.customer_publisher import publish_customer
from src.transformation.transformer import transform_order
from src.transformation.publisher import publish_order

from src.validation.validator import validate_order
from src.validation.quarantine import quarantine_record


def parse_source_timestamp(value):
    """Parse an ISO timestamp and normalize it to UTC."""

    if not value:
        return None

    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    except (TypeError, ValueError):
        return None


def run_ingestion(endpoint: str) -> dict:

    if endpoint not in {"customers", "orders"}:
        raise ValueError("Endpoint must be customers or orders")

    timestamp_field = (
        "created_at" if endpoint == "customers" else "updated_at"
    )

    run_id = str(uuid4())
    client = APIClient()

    with SessionLocal() as db:

        run = IngestionRun(
            run_id=run_id,
            status="running"
        )
        db.add(run)
        db.commit()

        input_count = 0
        output_count = 0
        rejected_count = 0
        seen_ids = set()

        try:
            # Resume an incomplete run using its saved cursor.
            checkpoint = get_checkpoint(db, endpoint)

            cursor = (
                checkpoint.next_cursor
                if checkpoint else None
            )

            # Keep the last successful watermark unchanged
            # until the complete ingestion run succeeds.
            watermark = (
                checkpoint.last_successful_watermark
                if checkpoint else None
            )

            max_source_timestamp = watermark

            for page in iter_pages(
                client,
                endpoint,
                start_cursor=cursor,
                updated_since=watermark
            ):

                records = page["records"]
                input_count += len(records)

                # Track the latest valid source timestamp.
                for record in records:
                    source_timestamp = parse_source_timestamp(
                        record.get(timestamp_field)
                    )

                    if (
                        source_timestamp is not None
                        and (
                            max_source_timestamp is None
                            or source_timestamp > max_source_timestamp
                        )
                    ):
                        max_source_timestamp = source_timestamp

                # Preserve the original API response.
                db.add(
                    RawAPIResponse(
                        run_id=run_id,
                        endpoint=endpoint,
                        page_number=page["page_number"],
                        request_cursor=page["request_cursor"],
                        next_cursor=page["next_cursor"],
                        http_status=200,
                        response_body=page["raw_response"],
                    )
                )

                if endpoint == "customers":

                    for record in records:
                        try:
                            with db.begin_nested():
                                transformed = transform_customer(record)
                                publish_customer(db, transformed)

                            output_count += 1

                        except Exception as exc:
                            quarantine_record(
                                db,
                                run_id,
                                endpoint,
                                record,
                                [str(exc)]
                            )
                            rejected_count += 1

                else:

                    known_customer_ids = set(
                        db.scalars(
                            select(Customer.customer_id)
                        ).all()
                    )

                    for record in records:

                        valid, reasons = validate_order(
                            record,
                            known_customer_ids,
                            seen_ids
                        )

                        if not valid:
                            quarantine_record(
                                db,
                                run_id,
                                endpoint,
                                record,
                                reasons
                            )
                            rejected_count += 1
                            continue

                        try:
                            with db.begin_nested():
                                transformed = transform_order(record)

                                publish_order(
                                    db,
                                    run_id,
                                    transformed
                                )

                            seen_ids.add(transformed["order_id"])
                            output_count += 1

                        except Exception as exc:
                            quarantine_record(
                                db,
                                run_id,
                                endpoint,
                                record,
                                [str(exc)]
                            )
                            rejected_count += 1

                # Save page data and the next cursor together.
                save_checkpoint(
                    db,
                    endpoint,
                    page["next_cursor"]
                )

                # Commit intermediate pages only.
                # Final page commits with successful run status.
                if page["next_cursor"] is not None:
                    db.commit()

            # Update the watermark only after all pages succeed.
            run.status = "completed"
            run.ended_at = datetime.now(timezone.utc)
            run.input_count = input_count
            run.output_count = output_count
            run.rejected_count = rejected_count

            mark_checkpoint_completed(
                db,
                endpoint,
                run_id,
                max_source_timestamp
            )

            # Commit final page, watermark and run status together.
            db.commit()

            return {
                "run_id": run_id,
                "endpoint": endpoint,
                "status": "completed",
                "input_count": input_count,
                "output_count": output_count,
                "rejected_count": rejected_count,
            }

        except Exception as exc:

            db.rollback()

            failed_run = db.get(IngestionRun, run_id)

            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.ended_at = datetime.now(timezone.utc)
                failed_run.input_count = input_count
                failed_run.output_count = output_count
                failed_run.rejected_count = rejected_count
                failed_run.error_message = str(exc)

                db.commit()

            raise

        finally:
            client.close()
