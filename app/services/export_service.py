from __future__ import annotations

import csv
import io

from openpyxl import Workbook
from sqlalchemy import select

import app.extensions as extensions
from app.models import Product


HEADERS = [
    "id", "title", "price", "currency", "rating",
    "category", "availability", "url",
]
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe_cell(value):
    """Prevent spreadsheet formula injection from scraped/untrusted text."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _rows(user_id: int):
    db = extensions.SessionLocal()
    try:
        products = db.scalars(
            select(Product)
            .where(Product.user_id == user_id)
            .order_by(Product.id.desc())
        ).all()
        return [
            [
                p.id, _safe_cell(p.title), p.price, _safe_cell(p.currency), p.rating,
                _safe_cell(p.category), _safe_cell(p.availability), _safe_cell(p.product_url),
            ]
            for p in products
        ]
    finally:
        db.close()


def csv_bytes(user_id: int) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(HEADERS)
    writer.writerows(_rows(user_id))
    return output.getvalue().encode("utf-8-sig")


def excel_bytes(user_id: int) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "products"
    ws.append(HEADERS)
    for row in _rows(user_id):
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
