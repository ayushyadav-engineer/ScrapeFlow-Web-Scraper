"""
=========================================================
File: main_controller.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

from flask import render_template

from app.repositories.scrape_repository import ScrapeRepository


class MainController:
    """
    Handles dashboard, home page and about page.
    """

    @staticmethod
    def home():
        """
        Display dashboard with statistics.
        """

        dashboard = ScrapeRepository.dashboard()

        latest_record = None

        history = ScrapeRepository.get_all()

        if history:
            latest_record = history[0]

        return render_template(
            "index.html",
            dashboard=dashboard,
            latest=latest_record,
            result=None
        )

    @staticmethod
    def about():
        """
        About page.
        """

        return render_template(
            "about.html"
        )

    @staticmethod
    def health():
        """
        Health check endpoint.
        """

        return {
            "application": "Web Scraping & Data Extraction System",
            "version": "1.0.0",
            "status": "Running"
        }

    @staticmethod
    def dashboard_data():
        """
        Return dashboard statistics.
        Useful for future AJAX updates.
        """

        dashboard = ScrapeRepository.dashboard()

        return {
            "total_websites": dashboard["websites"],
            "total_links": dashboard["links"],
            "total_images": dashboard["images"],
            "last_scrape": (
                dashboard["latest"].scraped_time.strftime(
                    "%d-%m-%Y %H:%M:%S"
                )
                if dashboard["latest"]
                else "No Data"
            )
        }