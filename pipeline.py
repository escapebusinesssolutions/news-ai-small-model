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
from same_day_dedup import TopicFingerprint, record_published_fingerprint, select_non_duplicate_topic
from insert_links import insert_affiliate_links
from publish import publish_article

SITE_URL = os.getenv("WORDPRESS_SITE_URL", "https://techsignal.wasmer.app").rstrip("/")
WP_POSTS_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
VALIDATION_PATH = Path("validation-report.json")


def load_existing_articles(limit: int = 100) -> list[dict[str, Any]]:
    """Read WordPress posts for lightweight internal-link discovery."""
    response = requests.get(WP_POSTS_URL, params={"per_page": min(limit, 100), "_fields": "title,link,slug"}, timeout=30)
    response.raise_for_status()
    posts = response.json()
    return [
        {
            "title": str(p.get("title", {}).get("rendered", "")),
            "url": p.get("link", ""),
            "slug": p.get("slug", ""),
        }
        for p in posts
        if p.get("title", {}).get("rendered") and p.get("link")
    ]


def build_validation_report(article: dict[str, Any], topic: dict[str, Any]) -> dict[str, Any]:
    """Build the pre-publish audit; publishing is blocked when it fails."""
    tracking_id = str(article.get("affiliate_tracking_id", ""))
    marketplace = str(article.get("affiliate_marketplace", ""))
    failures: list[str] = []
    links: list[dict[str, Any]] = []
    for product in article.get("products", []):
        name = str(product.get("name", "")).strip()
        url = str(product.get("affiliate_url", "")).strip()
        checks = {
            "has_url": bool(url),
            "amazon_uk": url.startswith("https://www.amazon.co.uk/") or url.startswith("https://amazon.co.uk/"),
            "tracking_id": bool(tracking_id) and f"tag={tracking_id}" in url,
        }
        if not all(checks.values()):
            failures.append(name or "unnamed product")
        links.append({"product": name, "asin_or_id": product.get("asin_or_id"), "affiliate_url": url, "affiliate_link_type": product.get("affiliate_link_type"), "checks": checks})
    if marketplace != "amazon.co.uk":
        failures.append("unsupported marketplace")
    if tracking_id != "echsignalnews-21":
        failures.append("unexpected tracking ID")
    return {
        "schema_version": "1.0",
        "stage": "pre_publish",
        "topic": topic,
        "article": {"title": article.get("title"), "slug": article.get("slug")},
        "affiliate": {"marketplace": marketplace, "tracking_id": tracking_id, "products_selected": len(links), "exact_catalogue_matches": article.get("affiliate_exact_matches", 0), "search_links": article.get("affiliate_search_links", 0), "links": links},
        "cross_links": article.get("cross_links", []),
        "validation": {"passed": not failures, "failures": failures},
    }


def write_validation_report(report: dict[str, Any], path: Path = VALIDATION_PATH) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_pipeline(topic: dict[str, Any], existing_articles: list[dict[str, Any]] | None = None, publish: bool = False, dedup: bool = False) -> dict[str, Any]:
    """Generate -> affiliate links -> cross-links -> pre-publish validation -> WordPress."""
    article = generate_article(topic)
    article = insert_affiliate_links(article)
    existing = existing_articles if existing_articles is not None else load_existing_articles()
    article = cross_link(article, existing)
    validation = build_validation_report(article, topic)
    write_validation_report(validation)
    if not validation["validation"]["passed"]:
        raise ValueError("Pre-publish validation failed: " + "; ".join(validation["validation"]["failures"]))
    if publish:
        article = publish_article(article)
        if dedup:
            record_published_fingerprint(TopicFingerprint.from_story_record({**topic, **article}))
    return {**article, "validation_report": validation}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic-index", type=int, default=0)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enable-dedup", action="store_true")
    args = parser.parse_args()
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    if args.topic_index < 0 or args.topic_index >= len(topics):
        raise SystemExit(f"topic index must be 0..{len(topics) - 1}")
    selected_index = args.topic_index
    selected_topic = topics[selected_index]
    if args.enable_dedup:
        selected_topic, selected_index = select_non_duplicate_topic(topics, args.topic_index)
        if selected_topic is None:
            report = {"schema_version": "1.0", "stage": "dedup_skip", "success": True, "published": False, "requested_topic_index": args.topic_index}
            target = args.output or VALIDATION_PATH
            write_validation_report(report, target)
            print(json.dumps(report, indent=2))
            return
    try:
        result = run_pipeline(selected_topic, publish=args.publish, dedup=args.enable_dedup)
    except Exception as exc:
        error_report = {"schema_version": "1.0", "stage": "pipeline_error", "topic": selected_topic, "success": False, "error": {"type": type(exc).__name__, "message": str(exc)}}
        target = args.output or VALIDATION_PATH
        write_validation_report(error_report, target)
        print(json.dumps(error_report, indent=2, ensure_ascii=False))
        raise
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
