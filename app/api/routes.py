from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import func, select

import app.extensions as extensions
from app.extensions import limiter
from app.models import Product, ScrapeJob
from app.security.request_validation import InputValidationError, strict_json_object, strict_query
from app.security.validation import ExportFormat, ProductSearchInput, ScrapeInput
from app.services.export_service import csv_bytes, excel_bytes
from app.services.scraper_service import ScrapeService

bp = Blueprint("api", __name__, url_prefix="/api")


def user_limit():
    return f"user:{current_user.get_id()}"


@bp.get("/csrf-token")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def csrf_token():
    from flask_wtf.csrf import generate_csrf
    return jsonify({"csrf_token": generate_csrf()})


@bp.get("/products")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def products():
    try:
        params = strict_query(request, {"q", "page"})
        if "page" in params:
            raw_page = params["page"]
            if not raw_page.isdigit() or len(raw_page) > 4:
                raise InputValidationError("Invalid page")
            params["page"] = int(raw_page)
        data = ProductSearchInput.model_validate(params)
    except (InputValidationError, ValidationError):
        return jsonify({"error": "Invalid query."}), 400

    db = extensions.SessionLocal()
    try:
        uid = int(current_user.get_id())
        page_size = 100
        query = select(Product).where(Product.user_id == uid)
        if data.q:
            query = query.where(Product.title.ilike(f"%{data.q}%"))
        rows = db.scalars(
            query.order_by(Product.id.desc())
            .offset((data.page - 1) * page_size)
            .limit(page_size)
        ).all()
        return jsonify({"items": [
            {
                "id": p.id, "title": p.title, "price": p.price,
                "currency": p.currency, "rating": p.rating,
                "category": p.category, "availability": p.availability,
                "url": p.product_url, "image_url": p.image_url,
            } for p in rows
        ], "page": data.page, "page_size": page_size})
    finally:
        db.close()


@bp.post("/scrape")
@login_required
@limiter.limit(lambda: current_app.config["RATE_SCRAPE_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_SCRAPE_USER"], key_func=user_limit, override_defaults=True)
def scrape():
    try:
        body = strict_json_object(request, {"url", "pages"})
        data = ScrapeInput.model_validate(body)
        if data.pages > current_app.config["SCRAPER_MAX_PAGES"]:
            raise ValueError("Page count exceeds configured limit")
        result = ScrapeService().scrape(int(current_user.get_id()), data.url, data.pages)
        return jsonify(result), 201
    except (InputValidationError, ValidationError, ValueError):
        return jsonify({"error": "Invalid scrape request."}), 400
    except Exception:
        return jsonify({"error": "Scrape could not be completed."}), 502


@bp.get("/scrape/jobs")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def jobs():
    db = extensions.SessionLocal()
    try:
        uid = int(current_user.get_id())
        rows = db.scalars(
            select(ScrapeJob).where(ScrapeJob.user_id == uid)
            .order_by(ScrapeJob.id.desc()).limit(100)
        ).all()
        return jsonify({"items": [
            {
                "id": j.id, "url": j.url, "status": j.status,
                "items": j.items_scraped, "duration": j.duration_seconds,
                "created_at": j.created_at.isoformat(),
            } for j in rows
        ]})
    finally:
        db.close()


@bp.get("/analytics")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def analytics():
    db = extensions.SessionLocal()
    try:
        uid = int(current_user.get_id())
        total = db.scalar(select(func.count(ScrapeJob.id)).where(ScrapeJob.user_id == uid)) or 0
        success = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == uid, ScrapeJob.status == "completed"
        )) or 0
        items = db.scalar(select(func.sum(ScrapeJob.items_scraped)).where(
            ScrapeJob.user_id == uid
        )) or 0
        today = datetime.now(timezone.utc).date()
        activity = []
        for offset in range(7):
            day = today - timedelta(days=6-offset)
            start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
            end = start + timedelta(days=1)
            count = db.scalar(select(func.count(ScrapeJob.id)).where(
                ScrapeJob.user_id == uid,
                ScrapeJob.created_at >= start,
                ScrapeJob.created_at < end,
            )) or 0
            activity.append({"label": day.strftime("%b %d"), "count": int(count)})
        return jsonify({
            "total_scrapes": int(total),
            "successful_scrapes": int(success),
            "total_items": int(items),
            "activity": activity,
        })
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

    uid = int(current_user.get_id())
    if data.fmt == "csv":
        return send_file(
            io.BytesIO(csv_bytes(uid)),
            mimetype="text/csv",
            as_attachment=True,
            download_name="scrapeflow-products.csv",
        )
    return send_file(
        io.BytesIO(excel_bytes(uid)),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="scrapeflow-products.xlsx",
    )
