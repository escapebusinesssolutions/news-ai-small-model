"""Run the complete Small Model content pipeline."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests

from cross_link import cross_link
from generate import generate_article, load_topics
from insert_links import insert_affiliate_links
from publish import publish_article

SITE_ID = os.getenv("WORDPRESS_SITE_ID", "51900195")
WP_POSTS_URL = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts/"


def load_existing_articles(limit: int = 100) -> list[dict[str, Any]]:
    """Read public WordPress posts for lightweight internal-link discovery."""
    response = requests.get(WP_POSTS_URL, params={"number": limit}, timeout=30)
    response.raise_for_status()
    posts = response.json().get("posts", [])
    return [
        {"title": p.get("title", ""), "url": p.get("URL", ""), "slug": p.get("slug", "")}
        for p in posts
        if p.get("title") and p.get("URL")
    ]


def run_pipeline(topic: dict[str, Any], existing_articles: list[dict[str, Any]] | None = None, publish: bool = False) -> dict[str, Any]:
    """Generate -> affiliate links -> cross-link -> WordPress."""
    article = generate_article(topic)
    article = insert_affiliate_links(article)
    existing = existing_articles if existing_articles is not None else load_existing_articles()
    article = cross_link(article, existing)

    if publish:
        article = publish_article(article)
    else:
        # Exercise the publisher conversion path without making a network write.
        article = {**article, "publish_result": publish_article(article)}
    return article


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic-index", type=int, default=0)
    parser.add_argument("--publish", action="store_true", help="Create the WordPress post using configured credentials")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    if args.topic_index < 0 or args.topic_index >= len(topics):
        raise SystemExit(f"topic index must be 0..{len(topics) - 1}")

    result = run_pipeline(topics[args.topic_index], publish=args.publish)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
