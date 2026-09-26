from __future__ import annotations

import logging
import time

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pydantic import ValidationError
from sqlalchemy import select

import app.extensions as extensions
from app.models import User
from app.security.backoff import ExponentialBackoff
from app.security.request_validation import InputValidationError, strict_form
from app.security.validation import LoginInput, RegisterInput
from app.extensions import limiter

bp = Blueprint("auth", __name__, url_prefix="/auth")
audit = logging.getLogger("security.audit")
backoff: ExponentialBackoff | None = None


def _backoff():
    global backoff
    if backoff is None:
        backoff = ExponentialBackoff(
            current_app.config["BACKOFF_BASE_SECONDS"],
            current_app.config["BACKOFF_MAX_SECONDS"],
            current_app.config["BACKOFF_RESET_SECONDS"],
        )
    return backoff


@bp.get("/register")
@limiter.limit(lambda: current_app.config["RATE_PUBLIC"], override_defaults=True)
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("auth/register.html")


@bp.post("/register")
@limiter.limit(lambda: current_app.config["RATE_REGISTER_IP"], override_defaults=True)
def register():
    ip = request.remote_addr or "unknown"
    key = f"register:{ip}"
    delay = _backoff().delay_for(key)
    if delay:
        time.sleep(delay)

    try:
        form = strict_form(
            request,
            {"email", "password", "confirm_password"},
            required={"email", "password", "confirm_password"},
        )
        data = RegisterInput.model_validate(form)
    except (InputValidationError, ValidationError):
        _backoff().failed(key)
        audit.warning("registration_validation_failed ip=%s", ip)
        flash("Please provide valid registration details.", "error")
        return render_template("auth/register.html"), 400

    email = str(data.email).lower()
    db = extensions.SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == email)):
            _backoff().failed(key)
            audit.warning("registration_validation_failed ip=%s", ip)
            flash("Registration could not be completed.", "error")
            return render_template("auth/register.html"), 400

        user = User(email=email)
        user.set_password(data.password)
        db.add(user)
        db.commit()
        _backoff().succeeded(key)
        audit.info("registration_success")
        return redirect(url_for("auth.login"))
    except Exception:
        db.rollback()
        _backoff().failed(key)
        audit.exception("registration_error")
        flash("Registration could not be completed.", "error")
        return render_template("auth/register.html"), 500
    finally:
        db.close()


@bp.get("/login")
@limiter.limit(lambda: current_app.config["RATE_PUBLIC"], override_defaults=True)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html")


@bp.post("/login")
@limiter.limit(lambda: current_app.config["RATE_AUTH_IP"], override_defaults=True)
@limiter.limit(
    lambda: current_app.config["RATE_AUTH_USER"],
    key_func=lambda: f"auth-user:{request.form.get('email', '').strip().lower()[:320]}",
    override_defaults=True,
)
def login_post():
    ip = request.remote_addr or "unknown"
    email_hint = str(request.form.get("email", "")).strip().lower()[:320]
    key = f"login:{ip}:{email_hint}"
    delay = _backoff().delay_for(key)
    if delay:
        time.sleep(delay)

    try:
        form = strict_form(request, {"email", "password"}, required={"email", "password"})
        data = LoginInput.model_validate(form)
    except (InputValidationError, ValidationError):
        _backoff().failed(key)
        audit.warning("login_failed ip=%s", ip)
        flash("Invalid email or password.", "error")
        return render_template("auth/login.html"), 400

    db = extensions.SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == str(data.email).lower()))
        valid = user is not None and user.check_password(data.password)

        if not valid:
            _backoff().failed(key)
            audit.warning("login_failed ip=%s", ip)
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html"), 401

        _backoff().succeeded(key)
        session.clear()
        session.permanent = True
        login_user(user, remember=False, fresh=True)
        audit.info("login_success user_id=%s", user.id)
        return redirect(url_for("dashboard.index"))
    finally:
        db.close()


@bp.post("/logout")
@login_required
@limiter.limit(lambda: current_app.config["RATE_USER_IP"], override_defaults=True)
@limiter.limit(lambda: current_app.config["RATE_USER"], key_func=lambda: f"user:{current_user.get_id()}", override_defaults=True)
def logout():
    audit.info("logout user_id=%s", current_user.get_id())
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
