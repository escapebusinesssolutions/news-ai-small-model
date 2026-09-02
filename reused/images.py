"""Acquire license-checked remote editorial images without storing them in WordPress."""
from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = ("public domain", "cc0", "cc by", "cc by-sa")


def _normalise_license(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key, {})
    if isinstance(value, dict):
        return str(value.get("value", "")).strip()
    return str(value).strip()


def _license_allowed(metadata: dict[str, Any]) -> bool:
    name = _normalise_license(_metadata_value(metadata, "LicenseShortName"))
    return any(name == allowed or name.startswith(allowed + " ") for allowed in ALLOWED_LICENSES)


def _clean_query(value: str) -> str:
    value = re.sub(r"[^\w\s+\-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()[:180]


def find_commons_image(search_query: str, timeout_seconds: int = 20) -> dict[str, Any] | None:
    """Find a Commons image whose licence is explicitly approved for reuse."""
    query = _clean_query(search_query)
    if not query:
        return None
    params = {
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": 6, "gsrlimit": 10,
        "prop": "imageinfo", "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 1400, "format": "json", "formatversion": 2,
    }
    response = requests.get(
        COMMONS_API, params=params, timeout=timeout_seconds,
        headers={"User-Agent": "TechSignal/1.0 (editorial image acquisition)"},
    )
    response.raise_for_status()
    for page in response.json().get("query", {}).get("pages", []):
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata") or {}
        mime = str(info.get("mime", "")).lower()
        if mime not in {"image/jpeg", "image/png", "image/webp"} or not _license_allowed(metadata):
            continue
        url = str(info.get("thumburl") or info.get("url") or "").strip()
        if not url.startswith("https://"):
            continue
        title = str(page.get("title", "")).removeprefix("File:")
        return {
            "url": url,
            "source_page": "https://commons.wikimedia.org/wiki/" + quote(str(page.get("title", "")), safe=""),
            "source": "Wikimedia Commons",
            "license": _metadata_value(metadata, "LicenseShortName"),
            "artist": re.sub(r"<[^>]+>", "", _metadata_value(metadata, "Artist")).strip(),
            "title": title,
            "mime": mime,
        }
    return None


def build_article_images(image_plan: list[dict[str, Any]], timeout_seconds: int = 20) -> list[dict[str, Any]]:
    """Resolve image concepts to verified remote images; never upload image bytes to WordPress."""
    resolved: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in image_plan:
        if not isinstance(item, dict):
            continue
        query = str(item.get("search_query") or item.get("query") or item.get("concept") or "").strip()
        image = find_commons_image(query, timeout_seconds=timeout_seconds)
        if not image or image["url"] in seen_urls:
            continue
        seen_urls.add(image["url"])
        resolved.append({
            "role": str(item.get("role", "context")).strip().lower() or "context",
            "url": image["url"],
            "alt_text": str(item.get("alt_text") or item.get("alt") or image["title"]).strip(),
            "caption": str(item.get("caption") or "").strip(),
            **image,
        })
    return resolved


def images_to_html(images: list[dict[str, Any]]) -> str:
    """Render externally hosted images with attribution; image bytes never enter WordPress Media."""
    figures: list[str] = []
    for image in images:
        src = html.escape(str(image["url"]), quote=True)
        alt = html.escape(str(image.get("alt_text", "")), quote=True)
        attribution = f"Source: {image['source']} — {image['license']}"
        if image.get("title"):
            attribution += f" — {image['title']}"
        if image.get("artist"):
            attribution += f" — {image['artist']}"
        attribution += f" — {image['source_page']}"
        caption = str(image.get("caption", "")).strip()
        caption_text = f"{caption} ({attribution})" if caption else attribution
        figures.append(
            '<figure class="techsignal-external-image">'
            f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async" />'
            f"<figcaption>{html.escape(caption_text, quote=False)}</figcaption>"
            "</figure>"
        )
    return "\n".join(figures)
