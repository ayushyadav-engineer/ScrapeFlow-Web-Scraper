"""
=========================================================
File: scraper_controller.py
Project: Web Scraping & Data Extraction System
=========================================================
"""

from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash
)

from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError
)

from app.models.scrape import Scrape
from app.repositories.scrape_repository import ScrapeRepository
from app.services.scraper_service import ScraperService
from app.services.parser_service import ParserService
from app.utils.validators import URLValidator
from app.utils.logger import logger


class ScraperController:
    """
    Handles complete scraping workflow.
    """

    @staticmethod
    def scrape():

        # ----------------------------------------
        # Get URL
        # ----------------------------------------

        url = request.form.get("url", "").strip()

        # ----------------------------------------
        # Validate URL
        # ----------------------------------------

        if not URLValidator.is_valid(url):

            flash(
                "Please enter a valid website URL.",
                "danger"
            )

            logger.warning(
                "Invalid URL entered: %s",
                url
            )

            return redirect(
                url_for("main.home")
            )

        try:

            # ----------------------------------------
            # Download Website
            # ----------------------------------------

            response = ScraperService.fetch(url)

            # ----------------------------------------
            # Parse HTML
            # ----------------------------------------

            data = ParserService.parse(response)

            # ----------------------------------------
            # Save into Database
            # ----------------------------------------

            scrape = Scrape(

                website_url=url,

                title=data["title"],

                description=data["description"],

                total_links=data["total_links"],

                total_images=data["total_images"],

                status=data["status"],

                http_status=data["http_status"]

            )

            ScrapeRepository.create(scrape)

            logger.info(
                "Website scraped successfully: %s",
                url
            )

            dashboard = ScrapeRepository.dashboard()

            flash(
                "Website scraped successfully.",
                "success"
            )

            return render_template(

                "index.html",

                dashboard=dashboard,

                result=data,

                latest=scrape

            )

        # ----------------------------------------
        # Timeout
        # ----------------------------------------

        except Timeout:

            logger.error(
                "Timeout while connecting to %s",
                url
            )

            flash(
                "Connection timed out.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )

        # ----------------------------------------
        # Connection Error
        # ----------------------------------------

        except ConnectionError:

            logger.error(
                "Connection refused: %s",
                url
            )

            flash(
                "Unable to connect to the website.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )

        # ----------------------------------------
        # Other Request Errors
        # ----------------------------------------

        except RequestException as error:

            logger.error(str(error))

            flash(
                "Website request failed.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )

        # ----------------------------------------
        # Unexpected Error
        # ----------------------------------------

        except Exception as error:

            logger.exception(error)

            flash(
                "Unexpected error occurred.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )