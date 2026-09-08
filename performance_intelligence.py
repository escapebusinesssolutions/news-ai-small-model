"""Classify Search Console evidence into actionable article signals."""
from __future__ import annotations

import statistics
from urllib.parse import urlsplit, urlunsplit


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def _canonical_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def classify_pages(performance: dict, posts: list[dict] | None = None) -> dict:
    """Return evidence-backed primary classifications without inventing commercial data."""
    posts_by_url = {
        _canonical_url(str(post.get("link"))): post
        for post in (posts or []) if post.get("link")
    }
    pages = performance.get("pages", [])
    impressions = [float(p.get("impressions", 0)) for p in pages]
    clicks = [float(p.get("clicks", 0)) for p in pages]
    ctrs = [float(p.get("ctr", 0)) for p in pages]
    p50_i = _percentile(impressions, 0.50)
    p75_i = _percentile(impressions, 0.75)
    p25_ctr = _percentile(ctrs, 0.25)
    p75_ctr = _percentile(ctrs, 0.75)
    p75_clicks = _percentile(clicks, 0.75)

    classified = []
    counts = {"traffic_winner": 0, "ctr_winner": 0, "underperformer": 0,
              "emerging_opportunity": 0, "normal": 0}
    for page in pages:
        url = str(page.get("page", ""))
        imp = float(page.get("impressions", 0))
        clk = float(page.get("clicks", 0))
        ctr = float(page.get("ctr", 0))
        if clk >= max(3.0, p75_clicks) and clk > 0:
            label = "traffic_winner"
        elif imp >= 20 and ctr >= max(0.01, p75_ctr):
            label = "ctr_winner"
        elif imp >= max(20.0, p75_i) and 0 < ctr < p25_ctr:
            label = "emerging_opportunity"
        elif imp >= max(20.0, p50_i) and clk == 0:
            label = "underperformer"
        else:
            label = "normal"
        counts[label] += 1
        post = posts_by_url.get(_canonical_url(url), {})
        classified.append({**page, "title": post.get("title", ""), "post_id": post.get("id"), "classification": label})

    return {
        "schema_version": "1.0",
        "thresholds": {"min_impressions": 20, "traffic_click_floor": 3},
        "counts": counts,
        "pages": classified,
        "commercial_data_status": "not_available_from_search_console",
    }
