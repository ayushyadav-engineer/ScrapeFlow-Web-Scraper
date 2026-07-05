"""
=========================================================
File: scrape_repository.py
Project: Web Scraping & Data Extraction System
Author: Ayush Yadav
=========================================================
"""

from sqlalchemy import func

from app.extensions import db
from app.models.scrape import Scrape


class ScrapeRepository:
    """
    Repository responsible for all
    database operations.
    """

    # ----------------------------------
    # CREATE
    # ----------------------------------

    @staticmethod
    def create(scrape):

        db.session.add(scrape)

        db.session.commit()

        return scrape

    # ----------------------------------
    # READ ALL
    # ----------------------------------

    @staticmethod
    def get_all():

        return (

            Scrape.query

            .order_by(

                Scrape.scraped_time.desc()

            )

            .all()

        )

    # ----------------------------------
    # READ ONE
    # ----------------------------------

    @staticmethod
    def get_by_id(record_id):

        return db.session.get(
            Scrape,
            record_id
        )

    # ----------------------------------
    # DELETE
    # ----------------------------------

    @staticmethod
    def delete(record_id):

        record = db.session.get(
            Scrape,
            record_id
        )

        if record:

            db.session.delete(record)

            db.session.commit()

            return True

        return False

    # ----------------------------------
    # SEARCH
    # ----------------------------------

    @staticmethod
    def search(keyword):

        keyword = keyword.strip()

        return (

            Scrape.query.filter(

                Scrape.website_url.ilike(
                    f"%{keyword}%"
                )

                |

                Scrape.title.ilike(
                    f"%{keyword}%"
                )

            )

            .order_by(

                Scrape.scraped_time.desc()

            )

            .all()

        )

    # ----------------------------------
    # PAGINATION
    # ----------------------------------

    @staticmethod
    def paginate(
        page=1,
        per_page=10
    ):

        return (

            Scrape.query

            .order_by(

                Scrape.scraped_time.desc()

            )

            .paginate(

                page=page,

                per_page=per_page,

                error_out=False

            )

        )

    # ----------------------------------
    # DASHBOARD
    # ----------------------------------

    @staticmethod
    def dashboard():

        total_websites = Scrape.query.count()

        total_links = (

            db.session.query(

                func.sum(

                    Scrape.total_links

                )

            ).scalar()

            or 0

        )

        total_images = (

            db.session.query(

                func.sum(

                    Scrape.total_images

                )

            ).scalar()

            or 0

        )

        latest = (

            Scrape.query

            .order_by(

                Scrape.scraped_time.desc()

            )

            .first()

        )

        return {

            "websites": total_websites,

            "links": total_links,

            "images": total_images,

            "latest": latest

        }

    # ----------------------------------
    # COUNT
    # ----------------------------------

    @staticmethod
    def count():

        return Scrape.query.count()

    # ----------------------------------
    # EXISTS
    # ----------------------------------

    @staticmethod
    def exists(url):

        return (

            Scrape.query.filter_by(

                website_url=url

            )

            .first()

            is not None

        )

    # ----------------------------------
    # UPDATE STATUS
    # ----------------------------------

    @staticmethod
    def update_status(
        record_id,
        status
    ):

        record = db.session.get(
            Scrape,
            record_id
        )

        if record:

            record.status = status

            db.session.commit()

            return True

        return False

    # ----------------------------------
    # CLEAR TABLE
    # ----------------------------------

    @staticmethod
    def clear():

        Scrape.query.delete()

        db.session.commit()