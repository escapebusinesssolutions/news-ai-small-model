from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "video_engine" / "techsignal" / "product_assets.json"
BRIEF_DIR = ROOT / "video_runs"


def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
    return [x.strip() for x in parts if x.strip()]


def _first(values: Any, fallback: str) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    return fallback


def _product_facts(product: dict[str, Any]) -> list[dict[str, str]]:
    specs = product.get("detailed_specs") or {}
    facts: list[dict[str, str]] = []
    for label, value in list(specs.items())[:3]:
        facts.append({"kind": "spec", "label": str(label).replace("_", " "), "value": str(value)})
    for value in list(product.get("differentiators", []))[:2]:
        facts.append({"kind": "advantage", "label": "WHY IT STANDS OUT", "value": str(value)})
    for value in list(product.get("known_limitations", []))[:2]:
        facts.append({"kind": "limitation", "label": "LIMITATION", "value": str(value)})
    return facts


def build_video_brief(article: dict[str, Any], topic: dict[str, Any]) -> Path:
    assets = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))["assets"]
    selected = article.get("products") or []
    if not selected:
        raise ValueError("video adapter requires at least one selected product")
    products = selected[:3]
    primary = products[0]
    asin = str(primary.get("asin_or_id", ""))
    asset = assets.get(asin)
    body_sentences = _sentences(str(article.get("body_markdown", "")))
    title = str(article.get("title") or topic.get("topic") or primary.get("name"))
    hook = body_sentences[0] if body_sentences else f"Is {primary.get('name')} actually the right choice for this buyer?"
    differentiator = _first(primary.get("differentiators"), "Its strongest differentiator is defined by the product catalogue.")
    use_case = _first(primary.get("use_cases"), "everyday tech use")
    limitation = _first(primary.get("known_limitations"), "Check the product limitations before buying.")
    best_for = ", ".join(primary.get("who_its_for", [])) or "buyers matching the intended use case"
    skip_if = ", ".join(primary.get("who_should_skip", [])) or "buyers with different requirements"
    verdict = _first(article.get("verdict"), body_sentences[-1] if body_sentences else f"{primary.get('name')} is worth considering when its strengths match your workflow.")
    beats = [
        {"arc": "hook", "text": hook},
        {"arc": "product", "text": f"{primary.get('name')} is the product being evaluated, not a generic category example."},
        {"arc": "key_feature", "text": differentiator},
        {"arc": "real_world_use", "text": f"Best use: {use_case}."},
        {"arc": "spec_check", "text": f"Key specification: {next(iter((primary.get('detailed_specs') or {}).values()), primary.get('price_range', 'see guide'))}."},
        {"arc": "tradeoff", "text": limitation},
        {"arc": "best_for", "text": f"Best for: {best_for}."},
        {"arc": "skip_if", "text": f"Skip if: {skip_if}."},
        {"arc": "verdict", "text": verdict},
    ]
    visual_facts: list[dict[str, str]] = []
    for p in products:
        visual_facts.append({"kind": "product", "label": "PRODUCT", "value": str(p.get("name"))})
        visual_facts.extend(_product_facts(p))
    visual_facts.append({"kind": "price", "label": "PRICE BAND", "value": str(primary.get("price_range", "not specified"))})
    visual_facts.append({"kind": "best_for", "label": "BEST FOR", "value": best_for})
    visual_facts.append({"kind": "skip_if", "label": "SKIP IF", "value": skip_if})
    visual_facts.append({"kind": "verdict", "label": "VERDICT", "value": verdict})
    brief = {
        "schema_version": "techsignal-video-brief-v2",
        "video_type": str(topic.get("intent", "buyer_guide")),
        "title": title,
        "topic": topic,
        "product": primary,
        "products": products,
        "primary_asset": asset,
        "script": {"beats": beats},
        "visual_facts": visual_facts[:24],
        "commercial_consistency": {
            "article_title": article.get("title"),
            "article_verdict": verdict,
            "selected_products": [p.get("asin_or_id") for p in products],
            "affiliate_exact_matches": article.get("affiliate_exact_matches", 0),
        },
    }
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    target = BRIEF_DIR / f"{primary.get('asin_or_id', 'product')}-video-brief.json"
    target.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return target
