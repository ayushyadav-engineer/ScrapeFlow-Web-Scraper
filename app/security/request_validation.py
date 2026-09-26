from __future__ import annotations

import json
from collections.abc import Iterable

from flask import Request


class InputValidationError(ValueError):
    """Raised when transport-level input is malformed before schema validation."""


def strict_form(request: Request, allowed: Iterable[str], required: Iterable[str] = ()) -> dict[str, str]:
    """Convert a form into a single-value dictionary and reject duplicates/unknown fields."""
    allowed_set = set(allowed)
    required_set = set(required)
    # Flask-WTF adds csrf_token to every protected form. CSRFProtect validates
    # it before the route executes, so the transport validator should accept
    # and discard that framework-managed field rather than treating it as an
    # unexpected application input.
    csrf_fields = {"csrf_token"}
    keys = set(request.form.keys())
    unexpected = keys - allowed_set - csrf_fields
    if unexpected:
        raise InputValidationError("Unexpected form field")

    result: dict[str, str] = {}
    for key in allowed_set:
        values = request.form.getlist(key)
        if len(values) > 1:
            raise InputValidationError("Duplicate form field")
        if values:
            result[key] = values[0]
        elif key in required_set:
            raise InputValidationError("Missing form field")
    return result


def strict_query(request: Request, allowed: Iterable[str]) -> dict[str, str]:
    """Convert query parameters into a single-value dictionary and reject duplicates."""
    allowed_set = set(allowed)
    if not set(request.args.keys()).issubset(allowed_set):
        raise InputValidationError("Unexpected query parameter")

    result: dict[str, str] = {}
    for key in allowed_set:
        values = request.args.getlist(key)
        if len(values) > 1:
            raise InputValidationError("Duplicate query parameter")
        if values:
            result[key] = values[0]
    return result


def strict_json_object(request: Request, allowed: Iterable[str]) -> dict:
    """Require a JSON object with no duplicate/unknown top-level fields."""
    if not request.is_json:
        raise InputValidationError("JSON content type required")

    duplicate = False

    def pairs_hook(pairs):
        nonlocal duplicate
        result = {}
        for key, value in pairs:
            if key in result:
                duplicate = True
                continue
            result[key] = value
        return result

    try:
        body = json.loads(request.get_data(cache=True), object_pairs_hook=pairs_hook)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InputValidationError("Malformed JSON") from exc

    if duplicate or not isinstance(body, dict):
        raise InputValidationError("JSON object required")
    allowed_set = set(allowed)
    if not set(body).issubset(allowed_set):
        raise InputValidationError("Unexpected JSON field")
    return body
