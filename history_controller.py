"""
=========================================================
File: history_controller.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from app.repositories.scrape_repository import ScrapeRepository
from app.utils.logger import logger


class HistoryController:
    """
    Handles all scraping history operations.
    """

    @staticmethod
    def history():
        """
        Display paginated scraping history.
        """

        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        pagination = ScrapeRepository.paginate(
            page=page,
            per_page=10
        )

        dashboard = ScrapeRepository.dashboard()

        return render_template(
            "history.html",
            pagination=pagination,
            dashboard=dashboard,
            keyword="",
            search_mode=False
        )

    @staticmethod
    def search():
        """
        Search history by title or website URL.
        """

        keyword = request.args.get(
            "keyword",
            ""
        ).strip()

        dashboard = ScrapeRepository.dashboard()

        if keyword == "":

            pagination = ScrapeRepository.paginate(
                page=1,
                per_page=10
            )

            return render_template(
                "history.html",
                pagination=pagination,
                dashboard=dashboard,
                keyword="",
                search_mode=False
            )

        results = ScrapeRepository.search(keyword)

        logger.info(
            "History search performed: %s",
            keyword
        )

        return render_template(
            "history.html",
            results=results,
            dashboard=dashboard,
            keyword=keyword,
            search_mode=True
        )

    @staticmethod
    def delete(record_id):
        """
        Delete a scraped record.
        """

        record = ScrapeRepository.get_by_id(record_id)

        if record is None:

            flash(
                "Record not found.",
                "warning"
            )

            logger.warning(
                "Delete failed. Record %s not found.",
                record_id
            )

            return redirect(
                url_for("history.history")
            )

        ScrapeRepository.delete(record_id)

        logger.info(
            "Record deleted successfully. ID=%s",
            record_id
        )

        flash(
            "Record deleted successfully.",
            "success"
        )

        return redirect(
            url_for("history.history")
        )

    @staticmethod
    def dashboard():
        """
        Return dashboard statistics.
        Useful for future AJAX requests.
        """

        dashboard = ScrapeRepository.dashboard()

        return dashboard