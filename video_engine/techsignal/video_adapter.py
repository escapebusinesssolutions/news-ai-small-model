from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "video_engine" / "techsignal" / "product_assets.json"
BRIEF_DIR = ROOT / "video_runs"


def _sentences(text: str) -> list[str]:
    import re
    clean = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
    return [x.strip() for x in parts if x.strip()]


def build_video_brief(article: dict[str, Any], topic: dict[str, Any]) -> Path:
    assets = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))["assets"]
    selected = article.get("products") or []
    if not selected:
        raise ValueError("video adapter requires at least one selected product")
    product = selected[0]
    asin = str(product.get("asin_or_id", ""))
    asset = assets.get(asin)
    if not asset:
        raise ValueError(f"no validated product-video asset registered for {asin}")
    facts = list(product.get("key_points", []))
    facts += [f"Price band: {product.get('price_range', 'not specified')}"]
    facts += list(product.get("differentiators", []))
    facts += list(product.get("known_limitations", []))
    facts += ["Best for: " + ", ".join(product.get("who_its_for", []))]
    facts += ["Skip if: " + ", ".join(product.get("who_should_skip", []))]
    body_sentences = _sentences(str(article.get("body_markdown", "")))
    beats = [
        {"arc": "hook", "text": body_sentences[0] if body_sentences else f"{product.get('name')} is the product under review."},
        {"arc": "context", "text": f"This guide evaluates {product.get('name')} for {topic.get('intent', 'buyer-intent')} use."},
        {"arc": "what_happened", "text": "The relevant product facts are compared against the buyer decision."},
        {"arc": "why_it_matters", "text": "The practical trade-offs determine whether the product fits the intended workflow."},
        {"arc": "whats_next", "text": "TechSignal gives a buyer-specific verdict and identifies when to skip the product."},
    ]
    brief = {
        "schema_version": "techsignal-video-brief-v1",
        "video_type": str(topic.get("intent", "buyer_guide")),
        "title": str(article.get("title") or topic.get("topic") or product.get("name")),
        "product": product,
        "primary_asset": asset,
        "script": {"beats": beats},
        "visual_facts": facts[:11],
    }
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    target = BRIEF_DIR / f"{product.get('asin_or_id', 'product')}-video-brief.json"
    target.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return target

