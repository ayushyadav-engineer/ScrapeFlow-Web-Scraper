from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, render_template
from flask_login import current_user, login_required
from app.extensions import limiter
from sqlalchemy import func, select

import app.extensions as extensions
from app.models import Product, ScrapeJob

bp = Blueprint("dashboard", __name__)

def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current else 0.0
    return round(((current - previous) / previous) * 100, 1)

@bp.get("/")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=lambda: f"user:{current_user.get_id()}", override_defaults=True)
def index():
    db = extensions.SessionLocal()
    try:
        user_id = int(current_user.get_id())
        now = datetime.now(timezone.utc)
        today = now.date()
        start = datetime.combine(today - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
        previous_start = start - timedelta(days=7)

        total_products = db.scalar(select(func.count(Product.id)).where(Product.user_id == user_id)) or 0
        total_scrapes = db.scalar(select(func.count(ScrapeJob.id)).where(ScrapeJob.user_id == user_id)) or 0
        successful = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.status == "completed"
        )) or 0
        success_rate = round((successful / total_scrapes) * 100, 1) if total_scrapes else 0
        avg_items = db.scalar(select(func.avg(ScrapeJob.items_scraped)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.status == "completed"
        )) or 0
        recent = db.scalars(
            select(ScrapeJob).where(ScrapeJob.user_id == user_id)
            .order_by(ScrapeJob.created_at.desc()).limit(8)
        ).all()
        total_duration = db.scalar(select(func.sum(ScrapeJob.duration_seconds)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.status == "completed"
        )) or 0
        total_items = db.scalar(select(func.sum(ScrapeJob.items_scraped)).where(
            ScrapeJob.user_id == user_id
        )) or 0

        daily = []
        for offset in range(7):
            day = today - timedelta(days=6-offset)
            day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            count = db.scalar(select(func.count(ScrapeJob.id)).where(
                ScrapeJob.user_id == user_id,
                ScrapeJob.created_at >= day_start,
                ScrapeJob.created_at < day_end,
            )) or 0
            daily.append({"label": day.strftime("%b %d"), "count": int(count)})

        current_jobs = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.created_at >= start
        )) or 0
        previous_jobs = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == user_id,
            ScrapeJob.created_at >= previous_start,
            ScrapeJob.created_at < start,
        )) or 0
        current_items = db.scalar(select(func.coalesce(func.sum(ScrapeJob.items_scraped), 0)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.created_at >= start
        )) or 0
        previous_items = db.scalar(select(func.coalesce(func.sum(ScrapeJob.items_scraped), 0)).where(
            ScrapeJob.user_id == user_id,
            ScrapeJob.created_at >= previous_start,
            ScrapeJob.created_at < start,
        )) or 0
        current_products = db.scalar(select(func.count(Product.id)).where(
            Product.user_id == user_id, Product.created_at >= start
        )) or 0
        previous_products = db.scalar(select(func.count(Product.id)).where(
            Product.user_id == user_id,
            Product.created_at >= previous_start,
            Product.created_at < start,
        )) or 0
        current_success = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.status == "completed", ScrapeJob.created_at >= start
        )) or 0
        previous_success = db.scalar(select(func.count(ScrapeJob.id)).where(
            ScrapeJob.user_id == user_id, ScrapeJob.status == "completed",
            ScrapeJob.created_at >= previous_start, ScrapeJob.created_at < start,
        )) or 0
        current_avg = (float(current_items) / float(current_jobs)) if current_jobs else 0.0
        previous_avg = (float(previous_items) / float(previous_jobs)) if previous_jobs else 0.0
        current_success_rate = (float(current_success) / float(current_jobs) * 100) if current_jobs else 0.0
        previous_success_rate = (float(previous_success) / float(previous_jobs) * 100) if previous_jobs else 0.0

        return render_template(
            "dashboard/dashboard.html",
            total_products=int(total_products),
            total_scrapes=int(total_scrapes),
            success_rate=success_rate,
            avg_items=round(float(avg_items), 1),
            recent=recent,
            total_duration=round(float(total_duration), 2),
            total_items=int(total_items),
            successful=int(successful),
            daily=daily,
            scrape_trend=_pct_change(float(current_jobs), float(previous_jobs)),
            product_trend=_pct_change(float(current_products), float(previous_products)),
            success_trend=_pct_change(current_success_rate, previous_success_rate),
            avg_items_trend=_pct_change(current_avg, previous_avg),
        )
    finally:
        db.close()
        # SessionLocal is a sessionmaker in this project, so close() is the lifecycle operation.
