"""Generate original, analytical buyer-intent affiliate articles from the curated catalogue."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from reused.ai_provider import generate_text

TOPICS_FILE = Path(__file__).with_name("topics.json")
PRODUCTS_FILE = Path(__file__).with_name("products.json")

SYSTEM_PROMPT = """You are the senior editorial writer for TechSignal, a professional technology buying-guide publication.

Write for one specific reader: an informed buyer who is skeptical of generic affiliate content and wants help making a decision.
The article must feel written by an editor with a point of view. It should explain what matters, why it matters, where the trade-offs are, and who should or should not buy.

STYLE RULES
- Open with the actual buying question, tension, or decision. Do not begin with generic statements such as "In today's world", "Whether you're a...", "If you're looking for...", "Choosing the right...", or "Technology has become...".
- Use concrete reasoning instead of filler. Explain consequences for a buyer, not just catalogue facts.
- Vary sentence length and paragraph rhythm. Avoid repetitive "X is... X is... X is..." constructions.
- Prefer specific, useful observations over adjectives such as "great", "amazing", "powerful", "excellent", or "perfect".
- Give the reader a clear editorial point of view. Opinions must be explicitly framed as TechSignal's judgement, not disguised as product facts.
- Discuss meaningful trade-offs. A recommendation should explain what the buyer gains and what they give up.
- Do not manufacture drama, fake controversy, or certainty.
- Do not write for search engines. Do not stuff keywords.
- Do not use Markdown tables. Do not create Markdown links; affiliate links are inserted separately.

SOURCE AND FACT RULES
The supplied product brief is the complete and exclusive source of product facts. You may not add specifications, features, software capabilities, variants, accessories, compatibility claims, prices, discounts, availability, awards, tests, reviews, rankings, or competitor comparisons that are not explicitly present in the brief.
You may reason from documented facts. For example, a listed use case can support a discussion of buyer fit. Clearly distinguish inference and editorial judgement from catalogue facts.
Never claim you tested a product or have personal experience.
Never invent a competing product. If the catalogue does not contain enough products for a requested comparison, say so and make the available evidence useful instead.
Do not present a catalogue marketing phrase as independently verified fact.

ARTICLE QUALITY
The article should normally be substantial rather than concise: target roughly 1,000-1,600 words where the available evidence supports it. Do not pad an article to hit a word count.
Use a strong structure appropriate to the intent. Possible sections include:
- the buying question / why this decision is difficult
- TechSignal's take
- what the documented product characteristics mean in practice
- strengths and limitations
- trade-offs
- comparison or decision criteria when supported
- who should buy
- who should skip it / where it is a poor fit
- alternatives only when the catalogue actually supports them
- final recommendation / bottom line
Do not force every section when it would repeat information.

IMAGE PLANNING
Every article must include an image_plan with at least one hero image concept. Images should add visual information or context rather than decorate empty space.
Use product imagery when the supplied product is the subject and a lawful product image source is available downstream. Otherwise specify a contextual editorial image concept.
Do not invent image URLs. Return search/generation subjects and useful alt text only.

OUTPUT
Return ONLY valid JSON with keys: title, slug, meta_description, body_markdown, products, image_plan.
Each selected product must use a name from the supplied brief and preserve its exact asin_or_id, price_range, and key_points.
"""

EDITOR_PROMPT = """Act as the senior editor receiving a first draft from another writer.

Rewrite the draft rather than merely commenting on it. Preserve only claims supported by the allowed product brief.
Your job is to make the article feel authored, useful, and commercially credible without becoming promotional.

EDITING PASS
1. Strengthen the opening so it starts with the buyer's real decision, not a generic introduction.
2. Remove filler, repetition, generic AI phrasing, and empty adjectives.
3. Make the article more analytical: explain practical implications, trade-offs, and buyer scenarios from the supplied evidence.
4. Add a clear TechSignal point of view where the evidence supports one. Label judgement as judgement.
5. Make the recommendation conditional and specific: who should buy, who should skip, and why.
6. For comparison intent, compare only products actually present in the brief. Do not invent missing competitors.
7. Keep useful uncertainty. If the catalogue cannot substantiate something, say that rather than guessing.
8. Improve sentence rhythm and paragraph flow. Avoid formulaic section headings where a more natural heading would work.
9. Keep the article substantial without padding it. Aim for roughly 1,000-1,600 words when the evidence supports that length.
10. Add or improve the image_plan. It must contain a hero concept and only useful contextual/product images. Never invent URLs.

Return ONLY valid JSON with: title, slug, meta_description, body_markdown, products, image_plan.
"""

BANNED_OPENINGS = (
    "in today's world",
    "in today’s world",
    "whether you're",
    "whether you’re",
    "if you're looking for",
    "if you’re looking for",
    "choosing the right",
    "technology has become",
)


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
        if str(product.get("category", "")).lower() == category:
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
        result = json.loads(cleaned[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError("AI response must be a JSON object")
    required = ("title", "body_markdown", "products", "image_plan")
    missing = [key for key in required if not result.get(key)]
    if missing:
        raise ValueError(f"AI response missing required fields: {', '.join(missing)}")
    if not isinstance(result["products"], list) or not result["products"]:
        raise ValueError("AI response products must be a non-empty array")
    if not isinstance(result["image_plan"], list) or not result["image_plan"]:
        raise ValueError("AI response image_plan must be a non-empty array")
    result.setdefault("meta_description", "")
    return result


def _validate_editorial_quality(article: dict[str, Any], product_brief: list[dict[str, Any]], topic: dict[str, Any]) -> None:
    """Deterministic publication-quality checks; factual QA remains source-bound."""
    body = str(article.get("body_markdown", "")).strip()
    if len(re.findall(r"\b\w+\b", body)) < 700:
        raise ValueError("Editorial quality gate failed: article is too thin")
    if len(article.get("image_plan", [])) < 1:
        raise ValueError("Editorial quality gate failed: no image plan")
    if not any(str(item.get("role", "")).lower() == "hero" for item in article["image_plan"] if isinstance(item, dict)):
        raise ValueError("Editorial quality gate failed: hero image is required")
    if body.lower().startswith(BANNED_OPENINGS):
        raise ValueError("Editorial quality gate failed: generic AI opening detected")

    allowed = {str(p.get("asin_or_id")): p for p in product_brief}
    for selected in article.get("products", []):
        asin = str(selected.get("asin_or_id", ""))
        if asin not in allowed:
            raise ValueError(f"Editorial quality gate failed: product {asin or 'unknown'} is outside the supplied brief")
        source = allowed[asin]
        for key in ("name", "price_range", "key_points"):
            if selected.get(key) != source.get(key):
                raise ValueError(f"Editorial quality gate failed: product field {key} was altered for {asin}")

    intent = str(topic.get("intent", "buyer_guide")).lower()
    if any(token in intent for token in ("comparison", "vs", "versus", "alternatives")) and len(product_brief) < 2:
        # A comparison request with one catalogue item must remain honest rather than fabricate a rival.
        if re.search(r"\b(vs\.?|versus|compared with|comparison)\b", body, re.I) and len(product_brief) == 1:
            raise ValueError("Editorial quality gate failed: unsupported product comparison")


def _generate_editorial_draft(name: str, topic: dict[str, Any], product_brief: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = f"""Write the first full editorial draft for this TechSignal topic.

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}

Editorial objective:
Give the reader a clear decision framework and a defensible TechSignal point of view. Do not merely restate the catalogue.

Allowed product brief (exclusive factual source):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Produce the complete article plus an image plan. The image plan must contain useful concepts, not URLs.
Return only the JSON object.
"""
    return _parse_json(generate_text(SYSTEM_PROMPT, prompt))


def _edit_draft(name: str, topic: dict[str, Any], product_brief: list[dict[str, Any]], draft: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""Edit this TechSignal article to publication quality.

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}

Allowed product brief (exclusive factual source):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

FIRST DRAFT:
{json.dumps(draft, ensure_ascii=False, indent=2)}

{EDITOR_PROMPT}
"""
    return _parse_json(generate_text(SYSTEM_PROMPT, prompt))


def generate_article(topic: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(topic, str):
        topic = {"topic": topic, "intent": "buyer_guide", "category": "general"}
    name = str(topic.get("topic", "")).strip()
    if not name:
        raise ValueError("Topic is empty")

    product_brief = build_product_brief(topic)

    # All topics, including single-product topics, now use the same editorial engine.
    # This removes the old hard-coded thin article path that made single-product pages lifeless.
    draft = _generate_editorial_draft(name, topic, product_brief)
    try:
        article = _edit_draft(name, topic, product_brief, draft)
    except ValueError as edit_error:
        # One bounded repair attempt handles malformed JSON without silently accepting a weak draft.
        repair_prompt = f"""Return the following edited TechSignal article as valid JSON only.

Allowed product brief:
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Edited output:
{draft}

Required keys: title, slug, meta_description, body_markdown, products, image_plan.
Preserve the article's substantive editorial analysis, but remove any unsupported product claims and any invented products.
"""
        try:
            article = _parse_json(generate_text(SYSTEM_PROMPT, repair_prompt))
        except ValueError as repair_error:
            raise ValueError(f"Editorial generation failed validation; edit error: {edit_error}; repair error: {repair_error}") from repair_error

    _validate_editorial_quality(article, product_brief, topic)
    article["source_topic"] = name
    article["category"] = topic.get("category", "general")
    article["product_brief"] = product_brief
    article["slug"] = _slug(name)
    article["editorial_engine"] = "v2"
    article["editorial_passes"] = 2
    return article


if __name__ == "__main__":
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.json is empty")
    print(json.dumps(generate_article(topics[0]), indent=2, ensure_ascii=False))
