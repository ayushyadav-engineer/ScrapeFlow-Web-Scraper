"""
=========================================================
File: export_routes.py
=========================================================
"""

from flask import Blueprint

from app.controllers.export_controller import (
    ExportController
)

export_bp = Blueprint(
    "export",
    __name__,
    url_prefix="/export"
)


@export_bp.route("/csv")
def export_csv():
    return ExportController.export_csv()


@export_bp.route("/excel")
def export_excel():
    return ExportController.export_excel()


@export_bp.route("/json")
def export_json():
    return ExportController.export_json()


@export_bp.route("/sql")
def export_sql():
    return ExportController.export_sql()