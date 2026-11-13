import time
import requests

from src.config import settings


class APIClient:
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self):
        self.base_url = settings.API_BASE_URL.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.API_TOKEN}",
            "Accept": "application/json"
        })

    def fetch_page(self, endpoint, cursor=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = {"page_size": settings.PAGE_SIZE}

        if cursor is not None:
            params["cursor"] = cursor

        for attempt in range(settings.MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=settings.REQUEST_TIMEOUT
                )

                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    if attempt == settings.MAX_RETRIES:
                        response.raise_for_status()

                    retry_after = response.headers.get("Retry-After")

                    try:
                        delay = float(retry_after) if retry_after else (
                            settings.RETRY_BACKOFF_SECONDS * (2 ** attempt)
                        )
                    except ValueError:
                        delay = settings.RETRY_BACKOFF_SECONDS * (2 ** attempt)

                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.RequestException:
                if attempt == settings.MAX_RETRIES:
                    raise

                delay = settings.RETRY_BACKOFF_SECONDS * (2 ** attempt)
                time.sleep(delay)

        raise RuntimeError("API request failed after all retry attempts")

    def close(self):
        self.session.close()
