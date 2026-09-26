from __future__ import annotations

from flask import Flask, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError

import app.extensions as extensions
from .config import Config
from .security.errors import register_error_handlers
from .security.headers import apply_security_headers
from .security.logging import init_logging, register_request_logging


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    Config.validate()

    import os
    os.makedirs(app.instance_path, exist_ok=True)

    extensions.init_db(app.config["DATABASE_URL"])

    # Flask-Limiter 4.x: configure through Flask config before init_app.
    app.config["RATELIMIT_STORAGE_URI"] = Config.RATELIMIT_STORAGE_URI
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    app.config["RATELIMIT_DEFAULT"] = [Config.RATE_PUBLIC]
    app.config["RATELIMIT_KEY_PREFIX"] = "scrapeflow"
    extensions.limiter.init_app(app)

    extensions.csrf.init_app(app)
    extensions.login_manager.init_app(app)
    extensions.login_manager.login_view = "auth.login"
    extensions.login_manager.login_message = "Please sign in to continue."

    init_logging(app)
    register_request_logging(app)

    @extensions.login_manager.user_loader
    def load_user(user_id):
        from .models import User
        db = extensions.SessionLocal()
        try:
            return db.get(User, int(user_id))
        except (ValueError, TypeError):
            return None
        finally:
            db.close()

    @app.after_request
    def security_headers(response):
        return apply_security_headers(response)

    @app.errorhandler(CSRFError)
    def csrf_error(exc):
        from flask import request, jsonify, render_template
        import logging
        rid = getattr(request, "request_id", "-")
        logging.getLogger("security.audit").warning(
            "csrf_validation_failed request_id=%s method=%s path=%s",
            rid, request.method, request.path,
        )
        if request.path.startswith("/api/"):
            return jsonify({"error": "CSRF validation failed.", "request_id": rid}), 400
        return render_template("error.html", request_id=rid), 400

    # Only a small, explicit allowlist of non-sensitive values is exposed to
    # Jinja. app.config as a whole must never be handed to templates, since it
    # contains SECRET_KEY, DATABASE_URL, and other server-only secrets.
    _TEMPLATE_SAFE_CONFIG_KEYS = ("SCRAPER_MAX_PAGES",)

    @app.context_processor
    def inject_config():
        safe_config = {k: app.config[k] for k in _TEMPLATE_SAFE_CONFIG_KEYS}
        return {"config": safe_config}

    @app.get("/health")
    @extensions.limiter.limit(lambda: app.config["RATE_HEALTH"], override_defaults=True)
    def health():
        return {"status": "ok"}

    from .auth.routes import bp as auth_bp
    from .dashboard.routes import bp as dashboard_bp
    from .history.routes import bp as history_bp
    from .scraper.routes import bp as scraper_bp
    from .api.routes import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(scraper_bp)
    app.register_blueprint(api_bp)

    # Route-level limits are declared in each blueprint. The default public
    # limit protects any endpoint that is not explicitly classified.
    register_error_handlers(app)
    return app
