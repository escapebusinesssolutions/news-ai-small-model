"""Acquire license-checked remote editorial images without storing them in WordPress."""
from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = ("public domain", "cc0", "cc by", "cc by-sa")

# Category-aware fallbacks. These are deliberately specific enough to prevent an
# unrelated generic fallback (for example, microphone imagery on a power article).
CATEGORY_FALLBACKS = {
    "audio": ("USB microphone", "podcast microphone", "studio microphone"),
    "webcams": ("webcam computer", "computer webcam", "video conference camera"),
    "storage": ("portable SSD", "external hard drive", "computer storage drive"),
    "power": ("power bank", "portable charger", "USB-C power bank"),
    "workspace": ("computer desk workspace", "desktop productivity", "office desk"),
}

CATEGORY_TERMS = {
    "audio": ("microphone", "mic", "podcast", "audio", "recording", "headphone", "headphones"),
    "webcams": ("webcam", "camera", "video", "conference", "zoom", "teams"),
    "storage": ("ssd", "storage", "drive", "hard", "disk", "backup"),
    "power": ("power", "bank", "charger", "charging", "battery", "usb", "laptop", "portable"),
    "workspace": ("desk", "desktop", "workspace", "computer", "productivity", "office"),
}


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


def _license_url(license_name: str) -> str:
    name = _normalise_license(license_name)
    if name == "cc0" or name.startswith("cc0 "):
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if name.startswith("cc by-sa"):
        match = re.search(r"(\d+(?:\.\d+)?)", name)
        version = match.group(1) if match else "4.0"
        return f"https://creativecommons.org/licenses/by-sa/{version}/"
    if name.startswith("cc by"):
        match = re.search(r"(\d+(?:\.\d+)?)", name)
        version = match.group(1) if match else "4.0"
        return f"https://creativecommons.org/licenses/by/{version}/"
    return ""


def _clean_query(value: str) -> str:
    value = re.sub(r"[^\w\s+\-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()[:180]


def _normalise_role(value: Any) -> str:
    """Map common model variants to the two roles used by the publisher."""
    role = str(value or "").strip().lower()
    if role.startswith("hero"):
        return "hero"
    return "context"


def _category_terms(category: str) -> tuple[str, ...]:
    key = str(category or "").strip().lower()
    return CATEGORY_TERMS.get(key, ())


def _image_is_category_relevant(image: dict[str, Any], category: str) -> bool:
    """Reject obviously unrelated Commons results before they reach WordPress."""
    terms = _category_terms(category)
    if not terms:
        return True
    haystack = f"{image.get('title', '')} {image.get('alt_text', '')}".lower()
    return any(term in haystack for term in terms)


def find_commons_image(search_query: str, timeout_seconds: int = 20, category: str = "") -> dict[str, Any] | None:
    """Find a Commons image whose licence and, when known, category are approved."""
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
        license_name = _metadata_value(metadata, "LicenseShortName")
        title = str(page.get("title", "")).removeprefix("File:")
        image = {
            "url": url,
            "source_page": "https://commons.wikimedia.org/wiki/" + quote(str(page.get("title", "")), safe=""),
            "source": "Wikimedia Commons",
            "license": license_name,
            "license_url": _license_url(license_name),
            "artist": re.sub(r"<[^>]+>", "", _metadata_value(metadata, "Artist")).strip(),
            "title": title,
            "mime": mime,
        }
        if _image_is_category_relevant(image, category):
            return image
    return None


def build_article_images(
    image_plan: list[dict[str, Any]],
    timeout_seconds: int = 20,
    category: str = "",
) -> list[dict[str, Any]]:
    """Resolve category-relevant, licence-checked remote images; never upload bytes to WordPress."""
    resolved: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    terms = _category_terms(category)

    def add_image(item: dict[str, Any], image: dict[str, Any], role: str | None = None) -> None:
        if image["url"] in seen_urls:
            return
        seen_urls.add(image["url"])
        resolved.append({
            "role": role or _normalise_role(item.get("role", "context")),
            "url": image["url"],
            "alt_text": str(item.get("alt_text") or item.get("alt") or image["title"]).strip(),
            "caption": str(item.get("caption") or "").strip(),
            **image,
        })

    for item in image_plan:
        if not isinstance(item, dict):
            continue
        query = str(item.get("search_query") or item.get("query") or item.get("concept") or "").strip()
        if not query:
            continue
        # The model may produce a visually plausible but semantically wrong query.
        # For known categories, force the search into the article's product domain.
        query_lower = query.lower()
        if terms and not any(term in query_lower for term in terms):
            query = f"{query} {terms[0]}"
        image = find_commons_image(query, timeout_seconds=timeout_seconds, category=category)
        if image:
            add_image(item, image)

    # Category-specific fallbacks replace the old global microphone fallback.
    fallback_queries = CATEGORY_FALLBACKS.get(str(category or "").strip().lower(), ())
    for query in fallback_queries:
        if len(resolved) >= 2:
            break
        image = find_commons_image(query, timeout_seconds=timeout_seconds, category=category)
        if image:
            add_image({
                "role": "context",
                "alt_text": query,
                "caption": f"Context image related to {query.lower()}.",
            }, image, role="context")

    if resolved and not any(image.get("role") == "hero" for image in resolved):
        resolved[0]["role"] = "hero"
    return resolved


def images_to_html(images: list[dict[str, Any]]) -> str:
    """Render externally hosted images with attribution; image bytes never enter WordPress Media."""
    figures: list[str] = []
    for image in images:
        src = html.escape(str(image["url"]), quote=True)
        alt = html.escape(str(image.get("alt_text", "")), quote=True)
        source_page = html.escape(str(image.get("source_page", "")), quote=True)
        license_name = html.escape(str(image.get("license", "")), quote=False)
        license_url = html.escape(str(image.get("license_url", "")), quote=True)
        attribution = f"Source: {image['source']}"
        if image.get("title"):
            attribution += f" — {image['title']}"
        if image.get("artist"):
            attribution += f" — {image['artist']}"
        attribution_html = html.escape(attribution, quote=False)
        if license_url:
            attribution_html += f' — License: <a href="{license_url}" rel="license noopener" target="_blank">{license_name}</a>'
        else:
            attribution_html += f" — License: {license_name}"
        if source_page:
            attribution_html += f' — <a href="{source_page}" rel="noopener" target="_blank">source</a>'
        caption = str(image.get("caption", "")).strip()
        caption_html = html.escape(caption, quote=False) + " (" + attribution_html + ")" if caption else attribution_html
        figures.append(
            '<figure class="techsignal-external-image">'
            f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async" />'
            f"<figcaption>{caption_html}</figcaption>"
            "</figure>"
        )
    return "\n".join(figures)
