"""Build the TechSignal distribution queue from live published WordPress content.

This is the synchronisation contract for WordPress and social publication. Direct social
publishing remains opt-in per channel and requires platform credentials; this module never
silently publishes when a channel is unconfigured.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SITE_URL = os.getenv("TECHSIGNAL_URL", "https://techsignal.wasmer.app").rstrip("/")
OUT = Path("data/social_distribution_queue.json")
CHANNELS = ("youtube", "tiktok", "facebook", "instagram", "linkedin")


def fetch_published_posts(per_page: int = 100) -> list[dict[str, Any]]:
    response = requests.get(
        f"{SITE_URL}/wp-json/wp/v2/posts",
        params={"status": "publish", "per_page": per_page, "_fields": "id,date,slug,link,title,status"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_queue(posts: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for post in posts:
        title = post.get("title", {}).get("rendered", "").strip()
        if not title:
            continue
        rows.append({
            "post_id": post["id"],
            "title": title,
            "wordpress_url": post.get("link"),
            "slug": post.get("slug"),
            "published_at": post.get("date"),
            "channels": {
                channel: {
                    "status": "awaiting_channel_authorization",
                    "published_url": None,
                }
                for channel in CHANNELS
            },
        })
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_url": SITE_URL,
        "policy": {
            "wordpress_is_content_source": True,
            "social_publish_requires_explicit_channel_authorization": True,
            "channel_specific_copy_required": True,
            "no_unconfigured_channel_publish": True,
        },
        "items": rows,
    }


def main() -> None:
    posts = fetch_published_posts()
    queue = build_queue(posts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(queue['items'])} TechSignal distribution records from {SITE_URL}")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
