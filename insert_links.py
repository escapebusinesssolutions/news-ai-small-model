"""Amazon UK affiliate-link insertion.

This module deliberately knows only about the catalogue and Amazon URL format.
It can later be replaced by a Creators API adapter without changing article generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

PRODUCTS_FILE = Path(__file__).with_name("products.json")


def load_catalogue() -> dict[str, Any]:
    data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    if data.get("marketplace") != "amazon.co.uk":
        raise ValueError("This affiliate adapter currently supports Amazon UK only")
    if not data.get("tracking_id"):
        raise ValueError("products.json is missing tracking_id")
    if not isinstance(data.get("products"), list):
        raise ValueError("products.json must contain a products array")
    return data


def build_affiliate_url(url: str, tracking_id: str) -> str:
    """Return an Amazon UK URL carrying the configured Associates tracking ID."""
    parsed = urlparse(url.strip())
    if parsed.netloc.lower() not in {"amazon.co.uk", "www.amazon.co.uk"}:
        raise ValueError("Only Amazon.co.uk product URLs are accepted")
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["tag"] = [tracking_id]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True), fragment=""))


def _matches(product: dict[str, Any], name: str) -> bool:
    candidate = str(product.get("name", "")).casefold()
    target = name.casefold()
    return candidate == target or candidate in target or target in candidate


def insert_affiliate_links(article: dict[str, Any]) -> dict[str, Any]:
    """Add approved Amazon links to product recommendations in an article."""
    catalogue = load_catalogue()
    products = catalogue["products"]
    linked_products: list[dict[str, Any]] = []
    body = str(article.get("body_markdown", ""))

    for recommendation in article.get("products", []):
        name = str(recommendation.get("name", "")).strip()
        match = next((p for p in products if _matches(p, name)), None)
        if not match:
            linked_products.append({**recommendation, "affiliate_url": None})
            continue
        affiliate_url = build_affiliate_url(match["url"], catalogue["tracking_id"])
        linked_products.append({**recommendation, "affiliate_url": affiliate_url})
        marker = f"[{name}]({affiliate_url})"
        if name and name not in body:
            body += f"\n\n**Recommended product:** {marker}"

    result = dict(article)
    result["body_markdown"] = body
    result["products"] = linked_products
    result["affiliate_marketplace"] = catalogue["marketplace"]
    result["affiliate_tracking_id"] = catalogue["tracking_id"]
    return result


def validate_amazon_url(url: str, tracking_id: str = "techsignal-20") -> bool:
    return build_affiliate_url(url, tracking_id).split("?", 1)[0].startswith("https://")
