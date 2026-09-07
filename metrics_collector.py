from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from scaling import load_state, evaluate_metrics, save_state

SITE_URL = os.getenv("TECHSIGNAL_URL", os.getenv("WORDPRESS_SITE_URL", "https://techsignal.wasmer.app")).rstrip("/")
WP_POSTS_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
RUN_METRICS = Path("data/run_metrics.json")
SEARCH_PERFORMANCE = Path("data/search_performance.json")


def wp_posts() -> list[dict]:
    r = requests.get(WP_POSTS_URL, params={"per_page": 100, "orderby": "date", "order": "desc", "status": "publish", "_fields": "date,link"}, timeout=30)
    r.raise_for_status()
    return r.json()


def gsc_access_token() -> str | None:
    direct = os.getenv("GSC_ACCESS_TOKEN")
    if direct:
        return direct
    client_id = os.getenv("GSC_CLIENT_ID")
    client_secret = os.getenv("GSC_CLIENT_SECRET")
    refresh_token = os.getenv("GSC_REFRESH_TOKEN")
    if not all((client_id, client_secret, refresh_token)):
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json().get("access_token")


def gsc_query(token: str, start: str, end: str, dimensions: list[str] | None = None, row_limit: int = 250) -> list[dict]:
    site = os.getenv("GSC_SITE_URL", SITE_URL)
    url = f"https://www.googleapis.com/webmasters/v3/sites/{quote(site, safe='')}/searchAnalytics/query"
    payload = {"startDate": start, "endDate": end, "dimensions": dimensions or [], "rowLimit": row_limit}
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("rows", [])


def collect_search_performance(token: str, start: str, end: str) -> dict:
    rows = gsc_query(token, start, end, dimensions=["page"], row_limit=250)
    pages = []
    for row in rows:
        keys = row.get("keys", [])
        if not keys:
            continue
        pages.append({
            "page": keys[0],
            "clicks": float(row.get("clicks", 0)),
            "impressions": float(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0)),
            "position": float(row.get("position", 0)),
        })
    pages.sort(key=lambda x: (-x["clicks"], -x["impressions"]))
    clicks = sum(x["clicks"] for x in pages)
    impressions = sum(x["impressions"] for x in pages)
    return {
        "schema_version": "1.0",
        "period": {"start": start, "end": end},
        "totals": {
            "clicks": clicks,
            "impressions": impressions,
            "ctr": clicks / impressions if impressions else 0.0,
        },
        "pages": pages,
    }


def inspect_indexing(token: str, posts: list[dict]) -> float:
    site = os.getenv("GSC_SITE_URL", SITE_URL)
    urls = [p.get("link") for p in posts if p.get("link")]
    if not urls:
        return 0.0
    checked = 0
    indexed = 0
    for url in urls[:100]:
        r = requests.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect", headers={"Authorization": f"Bearer {token}"}, json={"inspectionUrl": url, "siteUrl": site, "languageCode": "en-US"}, timeout=30)
        if r.status_code != 200:
            continue
        checked += 1
        result = r.json().get("inspectionResult", {}).get("indexStatusResult", {})
        if result.get("verdict") == "PASS" and result.get("coverageState", "").lower().startswith("submitted and indexed"):
            indexed += 1
    return indexed / checked if checked else 0.0


def run_quality_metrics() -> tuple[float, float]:
    if not RUN_METRICS.exists():
        return 0.0, 0.0
    try:
        rows = json.loads(RUN_METRICS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0.0, 0.0
    recent = rows[-50:]
    if not recent:
        return 0.0, 0.0
    passed = sum(1 for x in recent if x.get("validation_passed") is True)
    rejected = sum(1 for x in recent if x.get("dedup_rejected") is True)
    return passed / len(recent), rejected / len(recent)


def main() -> None:
    now = datetime.now(timezone.utc)
    posts = wp_posts()
    recent_cutoff = now - timedelta(days=30)
    recent_posts = []
    for post in posts:
        if not post.get("date"):
            continue
        parsed = datetime.fromisoformat(post["date"].replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if parsed >= recent_cutoff:
            recent_posts.append(post)
    quality, duplicate = run_quality_metrics()
    token = gsc_access_token()
    index_rate = 0.0
    traffic_change = 0.0
    gsc_available = bool(token)
    if token:
        try:
            index_rate = inspect_indexing(token, recent_posts)
            end = now.date()
            current_start = str(end - timedelta(days=6))
            current_end = str(end - timedelta(days=1))
            previous_start = str(end - timedelta(days=13))
            previous_end = str(end - timedelta(days=7))
            current_rows = gsc_query(token, current_start, current_end)
            previous_rows = gsc_query(token, previous_start, previous_end)
            current_clicks = float(current_rows[0].get("clicks", 0)) if current_rows else 0.0
            previous_clicks = float(previous_rows[0].get("clicks", 0)) if previous_rows else 0.0
            traffic_change = ((current_clicks - previous_clicks) / previous_clicks) if previous_clicks else (1.0 if current_clicks > 0 else 0.0)
            performance = collect_search_performance(token, current_start, current_end)
            SEARCH_PERFORMANCE.parent.mkdir(parents=True, exist_ok=True)
            SEARCH_PERFORMANCE.write_text(json.dumps(performance, indent=2) + "\n", encoding="utf-8")
        except requests.RequestException as exc:
            print(f"GSC unavailable: {exc}")
            gsc_available = False
    state = load_state()
    metrics = {"current_target": state.get("recommended_target", state.get("current_target", 5)), "validation_pass_rate": quality, "duplicate_rejection_rate": duplicate, "index_rate": index_rate, "affiliate_click_rate": 0.0, "traffic_7d_change": traffic_change, "published_posts": len(posts), "gsc_available": gsc_available}
    result = evaluate_metrics(metrics)
    save_state(result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
