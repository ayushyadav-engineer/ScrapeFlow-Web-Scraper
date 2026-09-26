from __future__ import annotations

import logging
import re
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import g, request


_SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret[_-]?key|api[_-]?key|access[_-]?token|client[_-]?secret)=([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
    re.compile(r"(?i)(csrf[_-]?token)=([^\s,;]+)"),
]


class RedactingFilter(logging.Filter):
    """Prevent accidental credential/token leakage into application logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
            for pattern in _SECRET_PATTERNS:
                message = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]", message)
            record.msg = message
            record.args = ()
        except Exception:
            # Logging must never break the request path.
            pass
        return True


def init_logging(app):
    log_dir = Path(app.instance_path) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / "scrapeflow.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.addFilter(RedactingFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    ))

    app.logger.addHandler(handler)
    logging.getLogger("security.audit").addHandler(handler)
    logging.getLogger("scrapeflow.errors").addHandler(handler)


def register_request_logging(app):
    @app.before_request
    def request_id():
        g.request_id = uuid.uuid4().hex
        request.request_id = g.request_id

    @app.after_request
    def response_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response
