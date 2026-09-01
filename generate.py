"""Generate original buyer-intent affiliate articles from the curated product catalogue."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from reused.ai_provider import generate_text

TOPICS_FILE = Path(__file__).with_name("topics.json")
PRODUCTS_FILE = Path(__file__).with_name("products.json")

SYSTEM_PROMPT = """You are the editorial writer for a practical technology buying-guide website.
Write for intelligent human readers who need a useful answer, not for search engines or affiliate clicks.
Sound natural, direct, specific, and conversational. Avoid generic AI filler, exaggerated certainty, repetitive phrasing, and marketing language.
Write original buyer-intent decision-support content, not a generic listicle.
The supplied product brief is the complete and exclusive source of product facts. You may not add specifications, features, software capabilities, variants, accessories, compatibility claims, prices, discounts, availability, awards, tests, reviews, rankings, or competitor comparisons that are not explicitly present in the brief.
You may make clearly framed editorial judgements about fit and trade-offs, but do not present those judgements as product facts.
Never claim you tested products or have personal experience. Never invent a competing product merely because the topic wording implies one exists.
Do not make unsupported absolute claims such as "best for everyone", "only option", "clear winner", or "punches above its price".
If the catalogue does not contain enough products for a literal comparison or alternatives request, say so plainly and turn the article into a useful guide to the available product rather than inventing alternatives.
Do not create Markdown links; affiliate links are inserted by a separate stage.
Return ONLY valid JSON with keys: title, slug, meta_description, body_markdown, products.
Each selected product must use a name from the supplied brief and preserve its exact asin_or_id, price_range, and key_points.
Do not use Markdown tables. Use headings, paragraphs, and bullet lists only.
"""


def load_topics() -> list[dict[str, Any]]:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    topics = data.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError("topics.json must contain a topics array")
    return topics


def load_product_catalogue() -> dict[str, Any]:
    data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    products = data.get("products", [])
    if not isinstance(products, list) or not products:
        raise ValueError("products.json must contain a non-empty products array")
    return data


def build_product_brief(topic: dict[str, Any]) -> list[dict[str, Any]]:
    """Select only curated catalogue facts relevant to the queued topic."""
    category = str(topic.get("category", "")).strip().lower()
    catalogue = load_product_catalogue()
    candidates = []
    for product in catalogue["products"]:
        product_category = str(product.get("category", "")).lower()
        if product_category == category:
            candidates.append({
                "name": product.get("name"),
                "asin_or_id": product.get("asin_or_id"),
                "price_range": product.get("price_range"),
                "use_cases": product.get("use_cases", []),
                "key_points": product.get("key_points", []),
            })
    if not candidates:
        raise ValueError(f"No curated catalogue products match topic category: {category or 'unknown'}")
    return candidates[:6]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("AI returned an empty response")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("AI returned invalid JSON: no JSON object found")
        try:
            result = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"AI returned invalid JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError("AI response must be a JSON object")
    required = ("title", "body_markdown", "products")
    missing = [key for key in required if not result.get(key)]
    if missing:
        raise ValueError(f"AI response missing required fields: {', '.join(missing)}")
    if not isinstance(result["products"], list) or not result["products"]:
        raise ValueError("AI response products must be a non-empty array")
    result.setdefault("meta_description", "")
    return result


def generate_article(topic: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(topic, str):
        topic = {"topic": topic, "intent": "buyer_guide", "category": "general"}
    name = str(topic.get("topic", "")).strip()
    if not name:
        raise ValueError("Topic is empty")
    product_brief = build_product_brief(topic)
    prompt = f"""Create one original buyer-intent article for this topic.

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}

The product brief below is the only source of product facts. Do not infer or import facts from memory or the web.

Product brief:
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Use only products from this brief. Preserve each selected product's exact name, asin_or_id, price_range, and key_points.
Use the supplied use_cases only as context for fit. Do not add technical specifications or product features that are not explicitly listed.
For comparison/alternatives topics, do not invent missing competitors. If only one relevant product exists, explicitly state that the current catalogue contains one directly relevant option and explain who it suits and what trade-off that creates.
Do not create Markdown links or Markdown tables.
Write a concise introduction, useful sections, practical trade-offs, a clear recommendation, and a short conclusion.
Return only the JSON object.
"""
    raw = generate_text(SYSTEM_PROMPT, prompt)
    try:
        article = _parse_json(raw)
    except ValueError as first_error:
        repair_prompt = f"""Repair this article into valid JSON while obeying the source-bound editorial rules.

Topic: {name}
Allowed product brief:
{json.dumps(product_brief, ensure_ascii=False, indent=2)}
Original model output:
{raw}

Return ONLY valid JSON with title, slug, meta_description, body_markdown, and products.
Products may ONLY come from the allowed brief and must preserve exact name, asin_or_id, price_range, and key_points.
Remove invented product facts, specifications, features, prices, availability, tests, awards, competitor products, Markdown links, and Markdown tables.
Do not claim personal testing. Do not invent missing alternatives.
"""
        try:
            article = _parse_json(generate_text(SYSTEM_PROMPT, repair_prompt))
        except ValueError as repair_error:
            raise ValueError(f"AI generation failed validation; initial error: {first_error}; repair error: {repair_error}") from repair_error
    article["source_topic"] = name
    article["category"] = topic.get("category", "general")
    article["product_brief"] = product_brief
    # The queue topic, not model wording, is the stable publication identity.
    article["slug"] = _slug(name)
    return article


if __name__ == "__main__":
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    print(json.dumps(generate_article(topics[0]), indent=2, ensure_ascii=False))
