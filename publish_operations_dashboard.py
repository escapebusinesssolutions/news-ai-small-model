"""Create or update the TechSignal operations dashboard as a WordPress draft."""
from __future__ import annotations

import os
from pathlib import Path

import requests

SITE = os.getenv("WORDPRESS_SITE_URL", os.getenv("TECHSIGNAL_URL", "https://techsignal.wasmer.app")).rstrip("/")
USERNAME = os.getenv("WORDPRESS_USERNAME", os.getenv("TECHSIGNAL_USERNAME", ""))
PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", os.getenv("TECHSIGNAL_APP_PASSWORD", ""))
SLUG = "techsignal-operations-dashboard"
TITLE = "TechSignal Operations Dashboard"


def main() -> None:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("WordPress username/application password not available")
    html = Path("operations-dashboard.html").read_text(encoding="utf-8")
    base = f"{SITE}/wp-json/wp/v2/posts"
    auth = (USERNAME, PASSWORD)
    lookup = requests.get(
        base,
        params={"slug": SLUG, "status": "draft,publish,future,pending,private", "context": "edit", "per_page": 100},
        auth=auth,
        timeout=30,
    )
    lookup.raise_for_status()
    payload = {"title": TITLE, "slug": SLUG, "content": html, "status": "draft"}
    existing = lookup.json()
    if not existing:
        # Some WordPress installations do not return drafts by slug reliably.
        # Fall back to an exact-title lookup so the dashboard remains one stable post.
        fallback = requests.get(
            base,
            params={"search": TITLE, "status": "draft,publish,future,pending,private", "context": "edit", "per_page": 100},
            auth=auth,
            timeout=30,
        )
        fallback.raise_for_status()
        existing = [post for post in fallback.json() if post.get("title", {}).get("raw") == TITLE]
    if existing:
        post_id = min(post["id"] for post in existing)
        response = requests.post(f"{base}/{post_id}", auth=auth, json=payload, timeout=30)
        action = "updated"
    else:
        response = requests.post(base, auth=auth, json=payload, timeout=30)
        action = "created"
    response.raise_for_status()
    data = response.json()
    print({"action": action, "post_id": data.get("id"), "status": data.get("status"), "link": data.get("link"), "edit_link": f"{SITE}/wp-admin/post.php?post={data.get('id')}&action=edit"})


if __name__ == "__main__":
    main()
