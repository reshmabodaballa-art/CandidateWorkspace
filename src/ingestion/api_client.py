
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from src.config import settings


class APIClient:
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self):
        self.base_url = settings.API_BASE_URL.rstrip("/")
        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"Bearer {settings.API_TOKEN}",
            "Accept": "application/json",
        })

        self.requests_per_second = float(
            settings.API_REQUESTS_PER_SECOND
        )

        if self.requests_per_second <= 0:
            raise ValueError(
                "API_REQUESTS_PER_SECOND must be greater than zero"
            )

        self.request_interval = 1.0 / self.requests_per_second
        self.next_request_time = 0.0
        self.rate_limit_lock = threading.Lock()

    def _wait_for_rate_limit(self):
        """Enforce the configured maximum request frequency."""

        with self.rate_limit_lock:
            current_time = time.monotonic()

            wait_time = max(
                0.0,
                self.next_request_time - current_time
            )

            if wait_time > 0:
                time.sleep(wait_time)

            self.next_request_time = (
                time.monotonic() + self.request_interval
            )

    def _get_retry_delay(self, response, attempt):
        """Calculate delay using Retry-After or exponential backoff."""

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    retry_time = parsedate_to_datetime(retry_after)

                    if retry_time.tzinfo is None:
                        retry_time = retry_time.replace(
                            tzinfo=timezone.utc
                        )

                    delay = (
                        retry_time - datetime.now(timezone.utc)
                    ).total_seconds()

                    return max(0.0, delay)

                except (TypeError, ValueError, OverflowError):
                    pass

        return settings.RETRY_BACKOFF_SECONDS * (2 ** attempt)

    def fetch_page(
        self,
        endpoint,
        cursor=None,
        updated_since=None
    ):
        """Fetch one API page with pagination and incremental filtering."""

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = {"page_size": settings.PAGE_SIZE}

        if cursor is not None:
            params["cursor"] = cursor

        if updated_since is not None:
            if isinstance(updated_since, datetime):
                updated_since = updated_since.isoformat()

            params["updated_since"] = updated_since

        for attempt in range(settings.MAX_RETRIES + 1):

            self._wait_for_rate_limit()

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=settings.REQUEST_TIMEOUT
                )

            except (requests.Timeout, requests.ConnectionError):
                if attempt == settings.MAX_RETRIES:
                    raise

                delay = (
                    settings.RETRY_BACKOFF_SECONDS * (2 ** attempt)
                )

                time.sleep(delay)
                continue

            if response.status_code in self.RETRYABLE_STATUS_CODES:
                if attempt == settings.MAX_RETRIES:
                    response.raise_for_status()

                delay = self._get_retry_delay(response, attempt)
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError(
            "API request failed after all retries"
        )

    def close(self):
        self.session.close()
