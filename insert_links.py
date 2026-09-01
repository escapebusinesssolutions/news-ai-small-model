"""Amazon UK affiliate-link insertion.

The product catalogue is the authoritative commercial inventory. Stage 2 may only
link products that can be resolved to an exact catalogue product and may only use
the Amazon product URL stored in that catalogue.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

PRODUCTS_FILE = Path(__file__).with_name("products.json")


def _amazon_asin(url: str) -> str | None:
    match = re.search(r"/dp/([A-Za-z0-9]{10})(?:[/?]|$)", urlparse(url.strip()).path)
    return match.group(1) if match else None


def load_catalogue() -> dict[str, Any]:
    data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    if data.get("marketplace") != "amazon.co.uk":
        raise ValueError("This affiliate adapter currently supports Amazon UK only")
    tracking_id = str(data.get("tracking_id", "")).strip()
    if not tracking_id:
        raise ValueError("products.json is missing tracking_id")
    products = data.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("products.json must contain a non-empty products array")
    seen_ids: set[str] = set()
    for product in products:
        name = str(product.get("name", "")).strip()
        asin = str(product.get("asin_or_id", "")).strip()
        url = str(product.get("url", "")).strip()
        if not name or not asin or not url or asin in seen_ids:
            raise ValueError(f"Invalid catalogue product: {name or asin or 'unnamed'}")
        parsed_asin = _amazon_asin(url)
        if parsed_asin != asin:
            raise ValueError(f"Catalogue product URL does not match asin_or_id: {name}")
        seen_ids.add(asin)
        if urlparse(url).netloc.lower() not in {"amazon.co.uk", "www.amazon.co.uk"}:
            raise ValueError(f"Catalogue product URL is not Amazon UK: {name}")
    return data


def build_affiliate_url(url: str, tracking_id: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.netloc.lower() not in {"amazon.co.uk", "www.amazon.co.uk"}:
        raise ValueError("Only Amazon.co.uk product URLs are accepted")
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["tag"] = [tracking_id]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True), fragment=""))


def _find_catalogue_product(products: list[dict[str, Any]], recommendation: dict[str, Any]) -> dict[str, Any] | None:
    requested_id = str(recommendation.get("asin_or_id", "")).strip()
    if requested_id:
        return next((p for p in products if str(p.get("asin_or_id", "")).strip() == requested_id), None)
    requested_name = str(recommendation.get("name", "")).strip().casefold()
    if not requested_name:
        return None
    matches = [p for p in products if str(p.get("name", "")).strip().casefold() == requested_name]
    return matches[0] if len(matches) == 1 else None


def _line_is_heading(body: str, position: int) -> bool:
    line_start = body.rfind("\n", 0, position) + 1
    return body[line_start:].startswith("#")


def _insert_product_link(body: str, product_name: str, affiliate_url: str) -> str:
    """Ensure the first body mention is one valid Markdown affiliate link."""
    marker = f"[{product_name}]({affiliate_url})"
    if marker in body:
        return body

    nested_pattern = re.compile(r"\[([^\]]+)\]\(\[(https?://[^\]]+)\]\((https?://[^)]+)\)\)")
    for match in nested_pattern.finditer(body):
        if match.group(1).strip().casefold() == product_name.casefold() and not _line_is_heading(body, match.start()):
            return body[:match.start()] + marker + body[match.end():]

    link_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    for match in link_pattern.finditer(body):
        if match.group(1).strip().casefold() == product_name.casefold() and not _line_is_heading(body, match.start()):
            return body[:match.start()] + marker + body[match.end():]

    linked_spans = [m.span() for m in link_pattern.finditer(body)]
    for match in re.finditer(re.escape(product_name), body, flags=re.IGNORECASE):
        start, end = match.span()
        if _line_is_heading(body, start):
            continue
        if not any(span_start <= start < span_end for span_start, span_end in linked_spans):
            return body[:start] + marker + body[end:]

    return f"{body}\n\n**Recommended product:** {marker}"


def insert_affiliate_links(article: dict[str, Any]) -> dict[str, Any]:
    catalogue = load_catalogue()
    products = catalogue["products"]
    linked_products: list[dict[str, Any]] = []
    body = str(article.get("body_markdown", ""))
    unmatched: list[str] = []
    recommendations = article.get("products", [])
    if not isinstance(recommendations, list) or not recommendations:
        raise ValueError("Article must contain at least one product recommendation")

    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            unmatched.append("invalid product record")
            continue
        name = str(recommendation.get("name", "")).strip()
        match = _find_catalogue_product(products, recommendation)
        if not match:
            unmatched.append(name or str(recommendation.get("asin_or_id", "")).strip() or "unnamed product")
            continue
        affiliate_url = build_affiliate_url(match["url"], catalogue["tracking_id"])
        body = _insert_product_link(body, match["name"], affiliate_url)
        linked_products.append({**recommendation, "name": match["name"], "asin_or_id": match["asin_or_id"], "affiliate_url": affiliate_url, "affiliate_link_type": "product"})

    if unmatched:
        raise ValueError("Article recommends products outside the approved catalogue: " + "; ".join(unmatched))
    result = dict(article)
    result["body_markdown"] = body
    result["products"] = linked_products
    result["affiliate_marketplace"] = catalogue["marketplace"]
    result["affiliate_tracking_id"] = catalogue["tracking_id"]
    result["affiliate_exact_matches"] = len(linked_products)
    result["affiliate_search_links"] = 0
    result["affiliate_unmatched_products"] = []
    return result


def validate_amazon_url(url: str, tracking_id: str = "echsignalnews-21") -> bool:
    affiliate_url = build_affiliate_url(url, tracking_id)
    parsed = urlparse(affiliate_url)
    return bool(_amazon_asin(affiliate_url) and parse_qs(parsed.query).get("tag") == [tracking_id])
