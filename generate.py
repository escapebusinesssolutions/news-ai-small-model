"""Generate buyer-intent affiliate articles from the Small Model topic queue."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from reused.ai_provider import generate_text

TOPICS_FILE = Path(__file__).with_name("topics.json")

SYSTEM_PROMPT = """You are the editorial writer for a practical technology buying-guide website.
Write useful, original buyer-intent content that helps a reader make a purchase decision.
Do not invent prices, specifications, tests, awards, availability, quotes, or personal experience.
Return ONLY valid JSON with these keys: title, slug, meta_description, body_markdown, products.
products must be a JSON array. Each product must contain name, why_it_is_relevant, and buying_note.
body_markdown must contain a concise introduction, useful recommendation/comparison sections, and a short conclusion.
"""


def load_topics() -> list[dict[str, Any]]:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    topics = data.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError("topics.json must contain a topics array")
    return topics


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
        # Some free models still wrap otherwise-valid JSON in a short preamble.
        # Extract the outermost JSON object without accepting arbitrary prose as content.
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
    result.setdefault("slug", _slug(str(result["title"])))
    result.setdefault("meta_description", "")
    return result


def generate_article(topic: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(topic, str):
        topic = {"topic": topic, "intent": "buyer_guide", "category": "general"}
    name = str(topic.get("topic", "")).strip()
    if not name:
        raise ValueError("Topic is empty")
    prompt = f"""Create one buyer-intent article for this topic:

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}

Prioritise practical buying advice and clear recommendations. Do not claim personal testing.
If exact current product facts are not supplied, describe selection criteria and avoid unsupported specifics.
Return only the JSON object. Do not add markdown fences, commentary, or explanation.
"""
    raw = generate_text(SYSTEM_PROMPT, prompt)
    article = _parse_json(raw)
    article["source_topic"] = name
    article["category"] = topic.get("category", "general")
    return article


if __name__ == "__main__":
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    print(json.dumps(generate_article(topics[0]), indent=2, ensure_ascii=False))
