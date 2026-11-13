
from collections.abc import Iterator
from typing import Any
from datetime import datetime


def iter_pages(
    client,
    endpoint: str,
    start_cursor: str | None = None,
    updated_since: datetime | None = None
) -> Iterator[dict[str, Any]]:
    """
    Fetch API pages using cursor pagination and an optional
    incremental watermark.

    The same watermark is applied to every page.
    """

    cursor = start_cursor
    page_number = 1
    seen_cursors = set()

    while True:
        if cursor is not None:
            if cursor in seen_cursors:
                raise RuntimeError(
                    f"Repeated pagination cursor detected: {cursor}"
                )

            seen_cursors.add(cursor)

        response = client.fetch_page(
            endpoint,
            cursor=cursor,
            updated_since=updated_since
        )

        if not isinstance(response, dict):
            raise ValueError(
                "API response must be a JSON object"
            )

        records = response.get("data")
        next_cursor = response.get("next_cursor")

        if not isinstance(records, list):
            raise ValueError(
                "API response must contain a data list"
            )

        if next_cursor is not None and not isinstance(next_cursor, str):
            raise ValueError(
                "next_cursor must be a string or null"
            )

        yield {
            "endpoint": endpoint,
            "page_number": page_number,
            "request_cursor": cursor,
            "next_cursor": next_cursor,
            "records": records,
            "raw_response": response
        }

        if next_cursor is None:
            break

        cursor = next_cursor
        page_number += 1
