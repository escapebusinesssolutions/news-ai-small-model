"""Apply the controlled TechSignal WordPress branding and verify the live header."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

SITE = os.environ["WORDPRESS_SITE_URL"].rstrip("/")
AUTH = (os.environ["WORDPRESS_USERNAME"], os.environ["WORDPRESS_APP_PASSWORD"])
TIMEOUT = 30
ASSET = Path("assets/logo.png")


def main() -> int:
    if not ASSET.exists():
        raise RuntimeError(f"Brand asset missing: {ASSET}")

    settings_url = f"{SITE}/wp-json/wp/v2/settings"
    settings = requests.get(settings_url, auth=AUTH, timeout=TIMEOUT)
    settings.raise_for_status()
    previous_logo = settings.json().get("site_logo", 0)

    with ASSET.open("rb") as handle:
        response = requests.post(
            f"{SITE}/wp-json/wp/v2/media",
            auth=AUTH,
            files={"file": (ASSET.name, handle, "image/png")},
            data={"title": "TechSignal Header Logo", "alt_text": "TechSignal"},
            timeout=TIMEOUT,
        )
    response.raise_for_status()
    media = response.json()
    media_id = int(media["id"])
    media_url = str(media.get("source_url", ""))

    update = requests.post(
        settings_url,
        auth=AUTH,
        json={"site_logo": media_id},
        timeout=TIMEOUT,
    )
    update.raise_for_status()

    page = requests.get(SITE + "/", timeout=TIMEOUT, headers={"User-Agent": "TechSignalBrandVerifier/1.0"})
    page.raise_for_status()
    html = page.text
    settings_after = requests.get(settings_url, auth=AUTH, timeout=TIMEOUT)
    settings_after.raise_for_status()
    actual_logo = settings_after.json().get("site_logo", 0)

    if actual_logo != media_id or (media_url and media_url not in html):
        requests.post(settings_url, auth=AUTH, json={"site_logo": previous_logo}, timeout=TIMEOUT).raise_for_status()
        raise RuntimeError(
            "Branding verification failed; site_logo was rolled back. "
            f"expected={media_id}, actual={actual_logo}, media_url_present={media_url in html if media_url else False}"
        )

    print(f"BRANDING_OK media_id={media_id} media_url={media_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
