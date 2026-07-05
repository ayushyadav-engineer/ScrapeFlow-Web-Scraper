"""
=========================================================
File: export_service.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

import os
import json
import pandas as pd

from config import OUTPUT_FOLDER
from app.repositories.scrape_repository import ScrapeRepository


class ExportService:
    """
    Handles exporting scraped data into multiple formats.
    """

    @staticmethod
    def _get_dataframe():
        """
        Load all database records into a Pandas DataFrame.
        """

        records = ScrapeRepository.get_all()

        data = []

        for row in records:

            data.append({

                "ID": row.id,

                "Website": row.website_url,

                "Title": row.title,

                "Description": row.description,

                "Links": row.total_links,

                "Images": row.total_images,

                "HTTP Status": row.http_status,

                "Status": row.status,

                "Scraped Time": row.scraped_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            })

        return pd.DataFrame(data)

    @staticmethod
    def export_csv():

        dataframe = ExportService._get_dataframe()

        filepath = os.path.join(
            OUTPUT_FOLDER,
            "scraped_data.csv"
        )

        dataframe.to_csv(
            filepath,
            index=False,
            encoding="utf-8"
        )

        return filepath

    @staticmethod
    def export_excel():

        dataframe = ExportService._get_dataframe()

        filepath = os.path.join(
            OUTPUT_FOLDER,
            "scraped_data.xlsx"
        )

        dataframe.to_excel(
            filepath,
            index=False
        )

        return filepath

    @staticmethod
    def export_json():

        dataframe = ExportService._get_dataframe()

        filepath = os.path.join(
            OUTPUT_FOLDER,
            "scraped_data.json"
        )

        dataframe.to_json(

            filepath,

            orient="records",

            indent=4

        )

        return filepath

    @staticmethod
    def export_sql():

        records = ScrapeRepository.get_all()

        filepath = os.path.join(

            OUTPUT_FOLDER,

            "scraped_data.sql"

        )

        with open(

            filepath,

            "w",

            encoding="utf-8"

        ) as sql_file:

            sql_file.write(

                "-- Web Scraper SQL Export\n\n"

            )

            for row in records:

                title = (

                    row.title or ""

                ).replace("'", "''")

                description = (

                    row.description or ""

                ).replace("'", "''")

                website = (

                    row.website_url or ""

                ).replace("'", "''")

                sql = f"""
INSERT INTO scraped_data
(
website_url,
title,
description,
total_links,
total_images,
status,
http_status
)
VALUES
(
'{website}',
'{title}',
'{description}',
{row.total_links},
{row.total_images},
'{row.status}',
{row.http_status}
);

"""

                sql_file.write(sql)

        return filepath