"""
=========================================================
File: scrape_routes.py
=========================================================
"""

from flask import Blueprint

from app.controllers.scraper_controller import (
    ScraperController
)

scrape_bp = Blueprint(
    "scrape",
    __name__
)


@scrape_bp.route(
    "/scrape",
    methods=["POST"]
)
def scrape():
    return ScraperController.scrape()