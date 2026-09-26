from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        # Development-only generated secret. Production validation below
        # refuses to start without an explicit secret.
        SECRET_KEY = secrets.token_urlsafe(48)

    ENV_NAME = os.getenv("FLASK_ENV", "development").lower()
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///scrapeflow.db")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    SESSION_LIFETIME_SECONDS = _int("SESSION_LIFETIME_SECONDS", 3600)
    MAX_REQUEST_BYTES = _int("MAX_REQUEST_BYTES", 1_048_576)

    RATE_AUTH_IP = os.getenv("RATE_AUTH_IP", "5/minute")
    RATE_AUTH_USER = os.getenv("RATE_AUTH_USER", "5/minute")
    RATE_REGISTER_IP = os.getenv("RATE_REGISTER_IP", "3/hour")
    RATE_PUBLIC = os.getenv("RATE_PUBLIC", "60/minute")
    RATE_HEALTH = os.getenv("RATE_HEALTH", "30/minute")
    RATE_USER = os.getenv("RATE_USER", "120/minute")
    RATE_USER_IP = os.getenv("RATE_USER_IP", "120/minute")
    RATE_SCRAPE_IP = os.getenv("RATE_SCRAPE_IP", "10/hour")
    RATE_SCRAPE_USER = os.getenv("RATE_SCRAPE_USER", "20/hour")
    RATE_EXPORT = os.getenv("RATE_EXPORT", "30/hour")
    RATE_EXPORT_IP = os.getenv("RATE_EXPORT_IP", "30/hour")

    BACKOFF_BASE_SECONDS = _float("BACKOFF_BASE_SECONDS", 1)
    BACKOFF_MAX_SECONDS = _float("BACKOFF_MAX_SECONDS", 32)
    BACKOFF_RESET_SECONDS = _float("BACKOFF_RESET_SECONDS", 900)

    SCRAPER_TIMEOUT_SECONDS = _int("SCRAPER_TIMEOUT_SECONDS", 15)
    SCRAPER_MAX_RESPONSE_BYTES = _int("SCRAPER_MAX_RESPONSE_BYTES", 2_097_152)
    SCRAPER_MAX_PAGES = _int("SCRAPER_MAX_PAGES", 20)
    SCRAPER_MAX_ITEMS = _int("SCRAPER_MAX_ITEMS", 500)
    SCRAPER_DELAY_SECONDS = _float("SCRAPER_DELAY_SECONDS", 0.5)
    SCRAPER_MAX_REDIRECTS = _int("SCRAPER_MAX_REDIRECTS", 5)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV_NAME == "production"
    PERMANENT_SESSION_LIFETIME = SESSION_LIFETIME_SECONDS

    MAX_CONTENT_LENGTH = MAX_REQUEST_BYTES

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        if cls.ENV_NAME == "production":
            secret = os.getenv("SECRET_KEY", "")
            if len(secret) < 32:
                raise RuntimeError("Production SECRET_KEY must be at least 32 characters.")
            if cls.RATELIMIT_STORAGE_URI.startswith("memory://"):
                raise RuntimeError("Production requires Redis-backed rate-limit storage.")
