"""
=========================================================
File: main_routes.py
=========================================================
"""

from flask import Blueprint

from app.controllers.main_controller import MainController

main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
def home():
    return MainController.home()


@main_bp.route("/about")
def about():
    return MainController.about()


@main_bp.route("/health")
def health():
    return MainController.health()


@main_bp.route("/dashboard")
def dashboard():
    return MainController.dashboard_data()