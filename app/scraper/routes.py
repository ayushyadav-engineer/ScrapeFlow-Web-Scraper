from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pydantic import ValidationError

import app.extensions as extensions
from app.extensions import limiter
from app.security.request_validation import InputValidationError, strict_form
from app.security.ssrf import SSRFBlocked
from app.security.validation import ScrapeInput
from app.services.scraper_service import ScrapeService

bp = Blueprint("scraper", __name__, url_prefix="/scrape")


def user_limit():
    return f"user:{current_user.get_id()}"


@bp.get("/")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=user_limit, override_defaults=True)
def page():
    return render_template("scraper/scrape.html")


@bp.post("/")
@login_required
@limiter.limit(lambda: current_app.config["RATE_SCRAPE_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_SCRAPE_USER"], key_func=user_limit, override_defaults=True)
def run():
    try:
        form = strict_form(request, {"url", "pages"}, required={"url", "pages"})
        raw_pages = form["pages"]
        if not raw_pages.isdigit() or len(raw_pages) > 4:
            raise InputValidationError("Invalid page count")
        form["pages"] = int(raw_pages)
        data = ScrapeInput.model_validate(form)
        if data.pages > current_app.config["SCRAPER_MAX_PAGES"]:
            raise ValueError("Page count exceeds configured limit")
        result = ScrapeService().scrape(int(current_user.get_id()), data.url, data.pages)
    except (InputValidationError, ValidationError, ValueError, SSRFBlocked):
        flash("Scrape could not be completed. Check the URL and options.", "error")
        return redirect(url_for("scraper.page"))
    except Exception:
        flash("Scrape could not be completed. Please try again.", "error")
        return redirect(url_for("scraper.page"))

    flash(f"Scrape completed: {result['items']} products extracted.", "success")
    return redirect(url_for("history.index"))
