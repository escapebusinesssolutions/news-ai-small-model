"""Apply controlled TechSignal WordPress logo and favicon branding."""
from __future__ import annotations

import os
from pathlib import Path

import requests

SITE = os.environ["WORDPRESS_SITE_URL"].rstrip("/")
AUTH = (os.environ["WORDPRESS_USERNAME"], os.environ["WORDPRESS_APP_PASSWORD"])
TIMEOUT = 30
ASSET = Path("assets/logo.png")
ICON = Path("assets/favicon.png")


def upload_media(path: Path, title: str, alt_text: str) -> dict:
    with path.open("rb") as handle:
        response = requests.post(
            f"{SITE}/wp-json/wp/v2/media",
            auth=AUTH,
            files={"file": (path.name, handle, "image/png")},
            data={"title": title, "alt_text": alt_text},
            timeout=TIMEOUT,
        )
    response.raise_for_status()
    return response.json()


def main() -> int:
    if not ASSET.exists():
        raise RuntimeError(f"Brand asset missing: {ASSET}")
    if not ICON.exists():
        raise RuntimeError(f"Brand asset missing: {ICON}")

    settings_url = f"{SITE}/wp-json/wp/v2/settings"
    settings = requests.get(settings_url, auth=AUTH, timeout=TIMEOUT)
    settings.raise_for_status()
    settings_json = settings.json()
    previous_logo = settings_json.get("site_logo", 0)
    previous_icon = settings_json.get("site_icon", 0)

    media = upload_media(ASSET, "TechSignal Header Logo", "TechSignal")
    media_id = int(media["id"])
    media_url = str(media.get("source_url", ""))

    icon_media = upload_media(ICON, "TechSignal Favicon", "TechSignal icon")
    icon_id = int(icon_media["id"])

    update = requests.post(
        settings_url,
        auth=AUTH,
        json={"site_logo": media_id, "site_icon": icon_id},
        timeout=TIMEOUT,
    )
    update.raise_for_status()

    page = requests.get(
        SITE + "/",
        timeout=TIMEOUT,
        headers={"User-Agent": "TechSignalBrandVerifier/1.0"},
    )
    page.raise_for_status()
    html = page.text

    settings_after = requests.get(settings_url, auth=AUTH, timeout=TIMEOUT)
    settings_after.raise_for_status()
    after_json = settings_after.json()
    actual_logo = after_json.get("site_logo", 0)
    actual_icon = after_json.get("site_icon", 0)

    if actual_logo != media_id or actual_icon != icon_id or (media_url and media_url not in html):
        requests.post(
            settings_url,
            auth=AUTH,
            json={"site_logo": previous_logo, "site_icon": previous_icon},
            timeout=TIMEOUT,
        ).raise_for_status()
        raise RuntimeError(
            "Branding verification failed; settings were rolled back. "
            f"logo_expected={media_id}, logo_actual={actual_logo}, "
            f"icon_expected={icon_id}, icon_actual={actual_icon}, "
            f"media_url_present={media_url in html if media_url else False}"
        )

    print(
        f"BRANDING_OK logo_media_id={media_id} icon_media_id={icon_id} "
        f"media_url={media_url}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
