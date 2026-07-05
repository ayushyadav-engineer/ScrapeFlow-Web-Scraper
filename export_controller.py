"""
=========================================================
File: export_controller.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

from flask import (
    flash,
    redirect,
    send_file,
    url_for
)

from app.services.export_service import ExportService
from app.utils.logger import logger


class ExportController:
    """
    Handles exporting scraped data.
    """

    @staticmethod
    def export_csv():

        try:

            filepath = ExportService.export_csv()

            logger.info(
                "CSV exported successfully."
            )

            return send_file(
                filepath,
                as_attachment=True
            )

        except Exception as error:

            logger.exception(error)

            flash(
                "Unable to export CSV.",
                "danger"
            )

            return redirect(
                url_for("history.history")
            )

    @staticmethod
    def export_excel():

        try:

            filepath = ExportService.export_excel()

            logger.info(
                "Excel exported successfully."
            )

            return send_file(
                filepath,
                as_attachment=True
            )

        except Exception as error:

            logger.exception(error)

            flash(
                "Unable to export Excel.",
                "danger"
            )

            return redirect(
                url_for("history.history")
            )

    @staticmethod
    def export_json():

        try:

            filepath = ExportService.export_json()

            logger.info(
                "JSON exported successfully."
            )

            return send_file(
                filepath,
                as_attachment=True
            )

        except Exception as error:

            logger.exception(error)

            flash(
                "Unable to export JSON.",
                "danger"
            )

            return redirect(
                url_for("history.history")
            )

    @staticmethod
    def export_sql():

        try:

            filepath = ExportService.export_sql()

            logger.info(
                "SQL backup exported successfully."
            )

            return send_file(
                filepath,
                as_attachment=True
            )

        except Exception as error:

            logger.exception(error)

            flash(
                "Unable to export SQL.",
                "danger"
            )

            return redirect(
                url_for("history.history")
            )