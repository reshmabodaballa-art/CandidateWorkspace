
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME = os.getenv(
        "APP_NAME", "YottaFlex API Data Engineering"
    )

    APP_ENV = os.getenv("APP_ENV", "development")

    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    API_TOKEN = os.getenv("API_TOKEN", "")

    API_BASE_URL = os.getenv(
        "API_BASE_URL", "http://127.0.0.1:8000/mock-api"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL", "sqlite:///./yottaflex.db"
    )

    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "100"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    API_REQUESTS_PER_SECOND = float(
        os.getenv("API_REQUESTS_PER_SECOND", "5")
    )

    RETRY_BACKOFF_SECONDS = float(
        os.getenv("RETRY_BACKOFF_SECONDS", "2")
    )


settings = Settings()
