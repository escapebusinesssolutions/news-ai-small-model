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
Write original buyer-intent decision-support content, not a generic listicle.
Use the supplied product brief as the only product-fact source. Do not invent prices, specifications, tests, awards, availability, quotes, or personal experience.
Never rewrite or paraphrase a competitor article. Do not claim you tested products.
For buyer-guide topics, use a clear "best X under Y" or similarly specific decision-support structure when the topic supports it. For comparison topics, use an explicit "X vs Y" decision structure.
Return ONLY valid JSON with these keys: title, slug, meta_description, body_markdown, products.
Each selected product must use a name from the supplied product brief and preserve its exact asin_or_id, price_range, and key_points. It may additionally contain why_it_is_relevant and buying_note.
body_markdown must contain a concise introduction, useful recommendation/comparison sections, and a short conclusion.
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
    query = str(topic.get("topic", "")).lower()
    catalogue = load_product_catalogue()
    candidates = []
    for product in catalogue["products"]:
        product_category = str(product.get("category", "")).lower()
        use_cases = " ".join(str(value) for value in product.get("use_cases", [])).lower()
        if product_category == category or category in use_cases or any(token in use_cases for token in query.split() if len(token) > 3):
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
    result.setdefault("slug", _slug(str(result["title"])))
    result.setdefault("meta_description", "")
    return result


def generate_article(topic: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(topic, str):
        topic = {"topic": topic, "intent": "buyer_guide", "category": "general"}
    name = str(topic.get("topic", "")).strip()
    if not name:
        raise ValueError("Topic is empty")
    product_brief = build_product_brief(topic)
    prompt = f"""Create one original buyer-intent article for this topic:

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}

Product brief (the only permitted source of product facts):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Use only products from this brief. Keep product names, asin_or_id, price_range, and key_points exactly as supplied.
Prioritise practical buying advice, trade-offs, fit-for-use, and clear recommendations.
Do not claim personal testing. Do not invent current prices; use the supplied price ranges only when useful.
Return only the JSON object. Do not add markdown fences, commentary, or explanation.
"""
    raw = generate_text(SYSTEM_PROMPT, prompt)
    article = _parse_json(raw)
    article["source_topic"] = name
    article["category"] = topic.get("category", "general")
    article["product_brief"] = product_brief
    return article


if __name__ == "__main__":
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    print(json.dumps(generate_article(topics[0]), indent=2, ensure_ascii=False))
