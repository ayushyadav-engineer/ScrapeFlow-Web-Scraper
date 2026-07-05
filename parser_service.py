"""
=========================================================
File: parser_service.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

from bs4 import BeautifulSoup


class ParserService:
    """
    Responsible for extracting structured
    information from HTML.
    """

    @staticmethod
    def parse(response):

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

        # -----------------------------
        # Website Title
        # -----------------------------

        title = "No Title"

        if soup.title and soup.title.string:

            title = soup.title.string.strip()

        # -----------------------------
        # Meta Description
        # -----------------------------

        description = "No Description"

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:

            description = meta.get(
                "content",
                "No Description"
            ).strip()

        # -----------------------------
        # Links
        # -----------------------------

        links = soup.find_all("a")

        total_links = len(links)

        internal_links = []

        external_links = []

        for link in links:

            href = link.get("href")

            if not href:

                continue

            if href.startswith("http"):

                external_links.append(href)

            else:

                internal_links.append(href)

        # -----------------------------
        # Images
        # -----------------------------

        images = soup.find_all("img")

        total_images = len(images)

        image_sources = []

        for image in images:

            src = image.get("src")

            if src:

                image_sources.append(src)

        # -----------------------------
        # Headings
        # -----------------------------

        headings = {}

        for level in range(1, 7):

            tag = f"h{level}"

            headings[tag] = [

                item.get_text(strip=True)

                for item in soup.find_all(tag)

            ]

        # -----------------------------
        # Paragraphs
        # -----------------------------

        paragraphs = [

            p.get_text(strip=True)

            for p in soup.find_all("p")

            if p.get_text(strip=True)

        ]

        # -----------------------------
        # Tables
        # -----------------------------

        total_tables = len(
            soup.find_all("table")
        )

        # -----------------------------
        # Forms
        # -----------------------------

        total_forms = len(
            soup.find_all("form")
        )

        # -----------------------------
        # Scripts
        # -----------------------------

        total_scripts = len(
            soup.find_all("script")
        )

        # -----------------------------
        # Return Structured Data
        # -----------------------------

        return {

            "title": title,

            "description": description,

            "status": "Success",

            "http_status": response.status_code,

            "total_links": total_links,

            "total_images": total_images,

            "internal_links": internal_links,

            "external_links": external_links,

            "image_sources": image_sources,

            "headings": headings,

            "paragraphs": paragraphs,

            "total_tables": total_tables,

            "total_forms": total_forms,

            "total_scripts": total_scripts

        }