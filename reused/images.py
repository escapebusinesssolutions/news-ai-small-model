"""Acquire license-checked remote editorial images without storing them in WordPress."""
from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = ("public domain", "cc0", "cc by", "cc by-sa")
FALLBACK_CONTEXT_QUERIES = (
    "desktop microphone recording",
    "microphone home studio",
    "person speaking microphone",
)


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
        license_name = _metadata_value(metadata, "LicenseShortName")
        title = str(page.get("title", "")).removeprefix("File:")
        return {
            "url": url,
            "source_page": "https://commons.wikimedia.org/wiki/" + quote(str(page.get("title", "")), safe=""),
            "source": "Wikimedia Commons",
            "license": license_name,
            "license_url": _license_url(license_name),
            "artist": re.sub(r"<[^>]+>", "", _metadata_value(metadata, "Artist")).strip(),
            "title": title,
            "mime": mime,
        }
    return None


def build_article_images(image_plan: list[dict[str, Any]], timeout_seconds: int = 20) -> list[dict[str, Any]]:
    """Resolve image concepts to verified remote images; never upload image bytes to WordPress."""
    resolved: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

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
        image = find_commons_image(query, timeout_seconds=timeout_seconds)
        if image:
            add_image(item, image)

    # If one planned image failed Commons search, use a lawful generic editorial
    # fallback so the article still has the required visual density.
    fallback_index = 0
    while len(resolved) < 2 and fallback_index < len(FALLBACK_CONTEXT_QUERIES):
        query = FALLBACK_CONTEXT_QUERIES[fallback_index]
        fallback_index += 1
        image = find_commons_image(query, timeout_seconds=timeout_seconds)
        if image:
            add_image({
                "role": "context",
                "alt_text": "Microphone used for voice recording at a desk",
                "caption": "Context image for a desktop voice-recording setup.",
            }, image, role="context")

    # A failed hero search must not turn an otherwise usable article into a failed
    # publication. Promote the first verified image to hero when necessary.
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
