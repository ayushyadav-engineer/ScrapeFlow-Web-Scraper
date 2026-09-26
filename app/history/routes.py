from __future__ import annotations

import io

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import func, select

import app.extensions as extensions
from app.extensions import limiter
from app.models import ScrapeJob
from app.security.request_validation import InputValidationError, strict_query
from app.security.validation import ExportFormat
from app.services.export_service import csv_bytes, excel_bytes

bp = Blueprint("history", __name__, url_prefix="/history")


def user_limit():
    return f"user:{current_user.get_id()}"


@bp.get("/")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def index():
    try:
        params = strict_query(request, {"page"})
        raw_page = params.get("page", "1")
        if not raw_page.isdigit() or len(raw_page) > 4:
            raise InputValidationError("Invalid page")
        page = int(raw_page)
        if page < 1 or page > 1000:
            raise InputValidationError("Invalid page")
    except InputValidationError:
        return jsonify({"error": "Invalid page."}), 400

    per_page = 20
    db = extensions.SessionLocal()
    try:
        user_id = int(current_user.get_id())
        total = db.scalar(select(func.count(ScrapeJob.id)).where(ScrapeJob.user_id == user_id)) or 0
        jobs = db.scalars(
            select(ScrapeJob).where(ScrapeJob.user_id == user_id)
            .order_by(ScrapeJob.created_at.desc())
            .offset((page - 1) * per_page).limit(per_page)
        ).all()
        return render_template(
            "history/history.html", jobs=jobs, page=page,
            has_next=(page * per_page < total),
        )
    finally:
        db.close()


@bp.get("/export/<fmt>")
@login_required
@limiter.limit(lambda: current_app.config["RATE_EXPORT_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_EXPORT"], key_func=user_limit, override_defaults=True)
def export(fmt):
    try:
        data = ExportFormat.model_validate({"fmt": fmt})
    except ValidationError:
        return jsonify({"error": "Unsupported export format."}), 400

    user_id = int(current_user.get_id())
    if data.fmt == "csv":
        return send_file(
            io.BytesIO(csv_bytes(user_id)),
            mimetype="text/csv",
            as_attachment=True,
            download_name="scrapeflow-products.csv",
        )
    return send_file(
        io.BytesIO(excel_bytes(user_id)),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="scrapeflow-products.xlsx",
    )
