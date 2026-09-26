from __future__ import annotations

from flask import current_app, request
from flask_login import current_user


def user_key():
    if getattr(current_user, "is_authenticated", False):
        return f"user:{current_user.get_id()}"
    return "anonymous"


def ip_user_key():
    if getattr(current_user, "is_authenticated", False):
        return f"{request.remote_addr or 'unknown'}:user:{current_user.get_id()}"
    return request.remote_addr or "unknown"


def init_rate_limit_config(app):
    app.config["RATELIMIT_STORAGE_URI"] = app.config["RATELIMIT_STORAGE_URI"]
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
