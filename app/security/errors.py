from __future__ import annotations

import logging

from flask import jsonify, render_template, request

log = logging.getLogger("scrapeflow.errors")


def register_error_handlers(app):
    def safe_response(status: int, *, limited: bool = False):
        request_id = getattr(request, "request_id", "-")
        if request.path.startswith("/api/"):
            message = "Too many requests." if limited else "Request could not be completed."
            return jsonify({"error": message, "request_id": request_id}), status
        return render_template(
            "error.html", request_id=request_id, limited=limited
        ), status

    def handle_expected(exc, status):
        request_id = getattr(request, "request_id", "-")
        # Expected HTTP errors are logged without exposing their internals to clients.
        log.warning(
            "HTTP error request_id=%s status=%s method=%s path=%s exception=%s",
            request_id, status, request.method, request.path, type(exc).__name__,
        )
        return safe_response(status)

    @app.errorhandler(400)
    def bad_request(exc):
        return handle_expected(exc, 400)

    @app.errorhandler(403)
    def forbidden(exc):
        return handle_expected(exc, 403)

    @app.errorhandler(404)
    def not_found(exc):
        return handle_expected(exc, 404)

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return handle_expected(exc, 405)

    @app.errorhandler(413)
    def too_large(exc):
        return handle_expected(exc, 413)

    @app.errorhandler(415)
    def unsupported_media(exc):
        return handle_expected(exc, 415)

    @app.errorhandler(422)
    def unprocessable(exc):
        return handle_expected(exc, 422)

    @app.errorhandler(429)
    def limited(exc):
        request_id = getattr(request, "request_id", "-")
        log.warning(
            "Rate limit exceeded request_id=%s method=%s path=%s",
            request_id, request.method, request.path,
        )
        return safe_response(429, limited=True)

    @app.errorhandler(500)
    def internal(exc):
        request_id = getattr(request, "request_id", "-")
        log.exception(
            "Unhandled server error request_id=%s method=%s path=%s",
            request_id, request.method, request.path,
        )
        return safe_response(500)

    @app.errorhandler(Exception)
    def unexpected(exc):
        request_id = getattr(request, "request_id", "-")
        log.exception(
            "Unhandled application exception request_id=%s method=%s path=%s",
            request_id, request.method, request.path,
        )
        return safe_response(500)
