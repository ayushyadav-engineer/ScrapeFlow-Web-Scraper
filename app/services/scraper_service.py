from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup, Tag
from flask import current_app
from sqlalchemy import select

import app.extensions as extensions
from app.models import Product, ScrapeJob
from app.security.ssrf import validate_url

log = logging.getLogger(__name__)
audit = logging.getLogger("security.audit")

CURRENCY_SYMBOLS = {
    "₹": "INR", "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
    "₩": "KRW", "₽": "RUB", "₺": "TRY", "₴": "UAH", "₫": "VND",
    "₱": "PHP", "฿": "THB", "₦": "NGN", "R$": "BRL", "A$": "AUD",
    "C$": "CAD", "HK$": "HKD", "SGD": "SGD", "AED": "AED",
}
CURRENCY_CODES = {
    "INR","USD","EUR","GBP","JPY","CNY","AUD","CAD","NZD","SGD","HKD",
    "AED","SAR","QAR","KWD","KRW","RUB","TRY","BRL","MXN","ZAR","CHF",
    "SEK","NOK","DKK","PLN","CZK","HUF","THB","PHP","VND","IDR","MYR",
    "NGN","UAH","ILS"
}

def clean(value, limit=2048):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:limit]


def parse_price(value):
    text = clean(value, 128)
    if not text:
        return None, ""
    currency = ""
    for symbol, code in sorted(CURRENCY_SYMBOLS.items(), key=lambda x: -len(x[0])):
        if symbol in text:
            currency = code
            break
    if not currency:
        match = re.search(r"\b([A-Z]{3})\b", text.upper())
        if match and match.group(1) in CURRENCY_CODES:
            currency = match.group(1)

    match = re.search(r"\d[\d,.\s]*\d|\d", text)
    if not match:
        return None, currency
    number = match.group(0).replace(" ", "")
    if "," in number and "." in number:
        number = number.replace(",", "") if number.rfind(".") > number.rfind(",") else number.replace(".", "").replace(",", ".")
    elif "," in number:
        parts = number.split(",")
        number = "".join(parts[:-1]) + "." + parts[-1] if len(parts[-1]) <= 2 else number.replace(",", "")
    try:
        value = float(Decimal(number))
    except (InvalidOperation, ValueError):
        return None, currency
    return (value if 0 <= value <= 1_000_000_000 else None), currency


def parse_rating(value):
    text = clean(value, 64).lower()
    word_map = {"one":1,"two":2,"three":3,"four":4,"five":5}
    for word, number in word_map.items():
        if word in text:
            return number
    m = re.search(r"([0-5](?:[.,]\d+)?)", text)
    if not m:
        return 0
    try:
        return max(0, min(5, round(float(m.group(1).replace(",", ".")))))
    except ValueError:
        return 0


def parse_availability(value):
    text = clean(value, 255)
    if not text:
        return ""
    low = re.sub(r"[\s_-]+", "", text.lower())
    mapping = {
        "instock":"In Stock", "available":"Available",
        "outofstock":"Out of Stock", "soldout":"Sold Out",
        "preorder":"Pre-Order", "backorder":"Back Order",
        "limitedavailability":"Limited Availability",
    }
    return mapping.get(low, text)


def absolute(base, href):
    if not href:
        return ""
    candidate = urljoin(base, clean(href, 2048))
    try:
        return validate_url(candidate)
    except Exception:
        return ""


def jsonld_objects(soup):
    result = []
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string or script.get_text()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                result.append(item)
                for key in ("@graph", "itemListElement"):
                    child = item.get(key)
                    if isinstance(child, list):
                        stack.extend(child)
                    elif isinstance(child, dict):
                        stack.append(child)
    return result


def extract_jsonld(soup, page_url):
    out = []
    for obj in jsonld_objects(soup):
        typ = str(obj.get("@type", "")).lower()
        if "product" not in typ and not any(k in obj for k in ("offers", "price", "priceCurrency")):
            continue
        offers = obj.get("offers", {})
        if isinstance(offers, list):
            offers = next((x for x in offers if isinstance(x, dict)), {})
        if not isinstance(offers, dict):
            offers = {}
        rating_obj = obj.get("aggregateRating") or {}
        price, detected_currency = parse_price(offers.get("price", obj.get("price")))
        currency = clean(offers.get("priceCurrency", obj.get("priceCurrency")), 8).upper() or detected_currency
        availability = parse_availability(offers.get("availability", obj.get("availability")))
        product_url = absolute(page_url, obj.get("url") or page_url) or page_url
        out.append({
            "title": clean(obj.get("name"), 512),
            "price": price,
            "currency": currency,
            "rating": parse_rating(rating_obj.get("ratingValue", obj.get("ratingValue", ""))),
            "category": clean(obj.get("category"), 255),
            "availability": availability,
            "product_url": product_url,
            "image_url": absolute(page_url, obj.get("image", "")),
        })
    return out


PRODUCT_SELECTORS = [
    "article.product_pod",
    "[itemtype*='Product']",
    ".product-card", ".product-item", ".product", ".product-tile",
    ".product-grid-item", ".product_box", ".item.product",
]


def extract_html_cards(soup, page_url):
    out = []
    seen = set()
    for selector in PRODUCT_SELECTORS:
        for node in soup.select(selector):
            if id(node) in seen:
                continue
            seen.add(id(node))

            title_node = node.select_one(
                "[itemprop='name'], h1, h2, h3, h4, .product-title, .product-name, .title, a[title]"
            )
            title = clean(
                (title_node.get("content") if title_node and title_node.get("content") else title_node.get_text(" ", strip=True) if title_node else ""),
                512,
            )
            if not title:
                continue

            price_node = node.select_one(
                "[itemprop='price'], .price_color, .price, .product-price, .current-price, .sale-price, .amount, [class*='price']"
            )
            raw_price = (
                price_node.get("content") if price_node and price_node.get("content")
                else price_node.get_text(" ", strip=True) if price_node else ""
            )
            price, currency = parse_price(raw_price)

            cur_node = node.select_one("[itemprop='priceCurrency'], [class*='currency']")
            if cur_node:
                explicit = clean(cur_node.get("content") or cur_node.get_text(" ", strip=True), 8).upper()
                if explicit in CURRENCY_CODES:
                    currency = explicit

            avail_node = node.select_one(
                "[itemprop='availability'], .availability, .stock, .instock, .in-stock, [class*='availability'], [class*='stock']"
            )
            availability = parse_availability(
                avail_node.get("content") if avail_node and avail_node.get("content")
                else avail_node.get_text(" ", strip=True) if avail_node else ""
            )

            rating_node = node.select_one(
                "[itemprop='ratingValue'], .star-rating, .rating, [class*='rating'], [class*='star-rating']"
            )
            rating = parse_rating(
                rating_node.get("content") if rating_node and rating_node.get("content")
                else rating_node.get_text(" ", strip=True) if rating_node else ""
            )

            link = node.select_one("a[href]")
            image = node.select_one("img")
            product_url = absolute(page_url, link.get("href") if link else page_url) or page_url
            image_url = absolute(page_url, (image.get("src") or image.get("data-src")) if image else "")

            # BooksToScrape and many catalogues expose category through breadcrumbs
            category_node = node.select_one("[itemprop='category'], .category, .product-category")
            category = clean(category_node.get_text(" ", strip=True) if category_node else "", 255)

            out.append({
                "title": title, "price": price, "currency": currency, "rating": rating,
                "category": category, "availability": availability,
                "product_url": product_url, "image_url": image_url,
            })
    return out


def extract_single(soup, page_url):
    title_node = soup.select_one("h1[itemprop='name'], h1.product-title, h1.product-name, h1, meta[property='og:title'], title")
    title = clean(
        title_node.get("content") if title_node and title_node.get("content") else title_node.get_text(" ", strip=True) if title_node else "",
        512,
    )
    if not title:
        return None
    price_node = soup.select_one("[itemprop='price'], meta[property='product:price:amount'], .price_color, .price, .product-price, .current-price, .sale-price")
    raw = price_node.get("content") if price_node and price_node.get("content") else price_node.get_text(" ", strip=True) if price_node else ""
    price, currency = parse_price(raw)
    cur = soup.select_one("[itemprop='priceCurrency'], meta[property='product:price:currency']")
    if cur:
        c = clean(cur.get("content") or cur.get_text(" ", strip=True), 8).upper()
        if c in CURRENCY_CODES:
            currency = c
    avail = soup.select_one("[itemprop='availability'], .availability, .stock, .instock, .in-stock, [class*='availability'], [class*='stock']")
    rating = soup.select_one("[itemprop='ratingValue'], .star-rating, .rating, [class*='rating']")
    return {
        "title": title, "price": price, "currency": currency,
        "rating": parse_rating(rating.get("content") if rating and rating.get("content") else rating.get_text(" ", strip=True) if rating else ""),
        "category": "", "availability": parse_availability(avail.get("content") if avail and avail.get("content") else avail.get_text(" ", strip=True) if avail else ""),
        "product_url": page_url, "image_url": absolute(page_url, soup.select_one("meta[property='og:image']").get("content") if soup.select_one("meta[property='og:image']") else ""),
    }


class ScrapeService:
    def _extract(self, soup, page_url, remaining):
        candidates = extract_jsonld(soup, page_url)
        if len(candidates) < remaining:
            candidates.extend(extract_html_cards(soup, page_url))
        if not candidates:
            one = extract_single(soup, page_url)
            if one:
                candidates.append(one)

        result, seen = [], set()
        for item in candidates:
            url = item.get("product_url", "")
            title = clean(item.get("title"), 512)
            if not url or not title or url in seen:
                continue
            seen.add(url)
            result.append({
                "title": title,
                "price": item.get("price"),
                "currency": clean(item.get("currency"), 8).upper(),
                "rating": max(0, min(5, int(item.get("rating") or 0))),
                "category": clean(item.get("category"), 255),
                "availability": parse_availability(item.get("availability")),
                "product_url": url,
                "image_url": clean(item.get("image_url"), 2048),
            })
            if len(result) >= remaining:
                break
        return result

    def scrape(self, user_id: int, raw_url: str, pages: int):
        url = validate_url(raw_url)
        cfg = current_app.config
        if pages < 1 or pages > cfg["SCRAPER_MAX_PAGES"]:
            raise ValueError("Invalid page count")

        db = extensions.SessionLocal()
        session = requests.Session()
        session.trust_env = False
        session.headers.update({
            "User-Agent": "ScrapeFlow/1.0 (+responsible scraping)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
        })
        max_redirects = int(cfg["SCRAPER_MAX_REDIRECTS"])
        started = time.monotonic()
        job = ScrapeJob(user_id=user_id, url=url, status="running")
        db.add(job)
        db.commit()
        db.refresh(job)
        audit.info("scrape_started user_id=%s job_id=%s", user_id, job.id)

        try:
            current = url
            products = []
            seen_pages = set()

            for _ in range(pages):
                current = validate_url(current)
                if current in seen_pages:
                    break
                seen_pages.add(current)

                response = None
                for redirect_count in range(max_redirects + 1):
                    response = session.get(
                        current, timeout=cfg["SCRAPER_TIMEOUT_SECONDS"],
                        allow_redirects=False, stream=True
                    )
                    if response.is_redirect or response.is_permanent_redirect:
                        if redirect_count >= max_redirects:
                            response.close()
                            raise ValueError("Too many redirects")
                        location = response.headers.get("Location")
                        response.close()
                        if not location:
                            raise ValueError("Unsafe redirect")
                        current = validate_url(urljoin(current, location))
                        continue
                    break
                if response is None:
                    raise ValueError("Request could not be completed")
                try:
                    response.raise_for_status()
                    validate_url(response.url)

                    content_type = response.headers.get("Content-Type", "").lower()
                    if "html" not in content_type and "xhtml" not in content_type:
                        raise ValueError("Target is not an HTML page")
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        if not content_length.isdigit():
                            raise ValueError("Invalid response length")
                        if int(content_length) > cfg["SCRAPER_MAX_RESPONSE_BYTES"]:
                            raise ValueError("Response is too large")

                    body = bytearray()
                    for chunk in response.iter_content(65536):
                        if chunk:
                            body.extend(chunk)
                            if len(body) > cfg["SCRAPER_MAX_RESPONSE_BYTES"]:
                                raise ValueError("Response is too large")
                finally:
                    response.close()
                    response = None

                soup = BeautifulSoup(bytes(body), "lxml")
                remaining = cfg["SCRAPER_MAX_ITEMS"] - len(products)
                if remaining <= 0:
                    break

                for item in self._extract(soup, current, remaining):
                    if item["product_url"] not in {x["product_url"] for x in products}:
                        products.append(item)
                    if len(products) >= cfg["SCRAPER_MAX_ITEMS"]:
                        break

                if len(products) >= cfg["SCRAPER_MAX_ITEMS"]:
                    break

                next_node = soup.select_one("a[rel='next'][href], li.next a[href]")
                if not next_node:
                    break
                next_url = absolute(current, next_node.get("href"))
                if not next_url:
                    break
                current = next_url
                if cfg["SCRAPER_DELAY_SECONDS"] > 0:
                    time.sleep(cfg["SCRAPER_DELAY_SECONDS"])

            for item in products:
                existing = db.scalar(select(Product).where(
                    Product.user_id == user_id,
                    Product.product_url == item["product_url"]
                ))
                if existing:
                    for key, value in item.items():
                        setattr(existing, key, value)
                else:
                    db.add(Product(user_id=user_id, **item))

            job.status = "completed"
            job.items_scraped = len(products)
            job.duration_seconds = round(time.monotonic() - started, 3)
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            audit.info("scrape_completed user_id=%s job_id=%s items=%s", user_id, job.id, job.items_scraped)

            return {
                "job_id": job.id,
                "items": len(products),
                "status": "completed",
                "duration_seconds": job.duration_seconds,
            }
        except Exception as exc:
            db.rollback()
            failed = db.get(ScrapeJob, job.id)
            if failed:
                failed.status = "failed"
                failed.error_message = str(exc)[:500]
                failed.duration_seconds = round(time.monotonic() - started, 3)
                failed.finished_at = datetime.now(timezone.utc)
                db.commit()
            log.exception("scrape_failed job_id=%s user_id=%s", job.id, user_id)
            audit.warning("scrape_failed user_id=%s job_id=%s", user_id, job.id)
            raise
        finally:
            session.close()
            db.close()
