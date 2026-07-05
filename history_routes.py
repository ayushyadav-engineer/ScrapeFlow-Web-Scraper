"""
=========================================================
File: history_routes.py
=========================================================
"""

from flask import Blueprint

from app.controllers.history_controller import (
    HistoryController
)

history_bp = Blueprint(
    "history",
    __name__,
    url_prefix="/history"
)


@history_bp.route("/")
def history():
    return HistoryController.history()


@history_bp.route("/search")
def search():
    return HistoryController.search()


@history_bp.route("/delete/<int:record_id>")
def delete(record_id):
    return HistoryController.delete(record_id)