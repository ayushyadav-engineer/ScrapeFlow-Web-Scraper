"""
=========================================================
File: scraper_service.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

import requests
from requests.exceptions import (
    HTTPError,
    Timeout,
    ConnectionError,
    RequestException
)


class ScraperService:
    """
    Handles downloading HTML from websites.
    """

    DEFAULT_TIMEOUT = 15

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    @classmethod
    def fetch(cls, url):
        """
        Download webpage HTML.

        Parameters
        ----------
        url : str

        Returns
        -------
        requests.Response
        """

        response = requests.get(
            url=url,
            headers=cls.HEADERS,
            timeout=cls.DEFAULT_TIMEOUT,
            allow_redirects=True
        )

        response.raise_for_status()

        return response

    @classmethod
    def get_html(cls, url):
        """
        Return HTML text only.
        """

        response = cls.fetch(url)

        return response.text

    @classmethod
    def get_status_code(cls, url):
        """
        Return HTTP status code.
        """

        response = cls.fetch(url)

        return response.status_code

    @classmethod
    def is_available(cls, url):
        """
        Check if website is reachable.
        """

        try:

            cls.fetch(url)

            return True

        except (
            HTTPError,
            Timeout,
            ConnectionError,
            RequestException
        ):

            return False

    @classmethod
    def get_headers(cls, url):
        """
        Return response headers.
        """

        response = cls.fetch(url)

        return dict(response.headers)

    @classmethod
    def get_content_type(cls, url):
        """
        Return Content-Type header.
        """

        response = cls.fetch(url)

        return response.headers.get(
            "Content-Type",
            "Unknown"
        )