"""Collect zero-cost publishing, indexing, and demand metrics for adaptive scaling."""
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


def gsc_query(token: str, start: str, end: str) -> dict:
    site = os.getenv("GSC_SITE_URL", SITE_URL)
    url = f"https://www.googleapis.com/webmasters/v3/sites/{quote(site, safe='')}/searchAnalytics/query"
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"startDate": start, "endDate": end, "dimensions": [], "rowLimit": 1}, timeout=30)
    r.raise_for_status()
    rows = r.json().get("rows", [])
    return rows[0] if rows else {"clicks": 0, "impressions": 0}


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
    recent_posts = [p for p in posts if p.get("date") and datetime.fromisoformat(p["date"].replace("Z", "+00:00")) >= recent_cutoff]
    quality, duplicate = run_quality_metrics()
    token = gsc_access_token()
    index_rate = 0.0
    traffic_change = 0.0
    gsc_available = bool(token)
    if token:
        try:
            index_rate = inspect_indexing(token, recent_posts)
            end = now.date()
            current = gsc_query(token, str(end - timedelta(days=6)), str(end - timedelta(days=1)))
            previous = gsc_query(token, str(end - timedelta(days=13)), str(end - timedelta(days=7)))
            prev_clicks = float(previous.get("clicks", 0))
            traffic_change = ((float(current.get("clicks", 0)) - prev_clicks) / prev_clicks) if prev_clicks else (1.0 if current.get("clicks", 0) > 0 else 0.0)
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
