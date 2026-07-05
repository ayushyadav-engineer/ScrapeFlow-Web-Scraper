from datetime import datetime

from app.extensions import db


class Scrape(db.Model):

    __tablename__ = "scraped_data"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    website_url = db.Column(
        db.String(500),
        nullable=False
    )

    title = db.Column(
        db.String(500)
    )

    description = db.Column(
        db.Text
    )

    total_links = db.Column(
        db.Integer,
        default=0
    )

    total_images = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(20),
        default="Success"
    )

    http_status = db.Column(
        db.Integer,
        default=200
    )

    scraped_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):

        return {

            "id": self.id,

            "website_url": self.website_url,

            "title": self.title,

            "description": self.description,

            "total_links": self.total_links,

            "total_images": self.total_images,

            "status": self.status,

            "http_status": self.http_status,

            "scraped_time": self.scraped_time

        }

    def __repr__(self):

        return f"<Scrape {self.website_url}>"