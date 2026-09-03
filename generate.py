"""Generate original, analytical buyer-intent affiliate articles from the curated catalogue."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from reused.ai_provider import generate_text
from topic_engine import expand_topics

TOPICS_FILE = Path(__file__).with_name("topics.json")
PRODUCTS_FILE = Path(__file__).with_name("products.json")

SYSTEM_PROMPT = """You are the senior editorial writer for TechSignal, a professional technology buying-guide publication.

Write for one specific reader: an informed buyer skeptical of generic affiliate content who wants help making a decision. The article must have a clear TechSignal point of view.

CORE RULES
- Start with the actual buying question, tension, scenario, or decision. Never open with generic AI framing such as "In today's world", "Whether you're...", "If you're looking for...", "Choosing the right...", or "Technology has become...".
- This is a decision aid, not a product-data dump. Connect important facts to buyer consequences.
- State a clear judgement. Avoid endless "it depends" language; explain exactly what condition changes the answer.
- Make trade-offs explicit: what the buyer gains, what they give up, and who should care.
- Prefer concrete observations over empty adjectives. Vary sentence rhythm and paragraph structure.
- Do not manufacture drama, fake controversy, certainty, tests, personal experience, or search-engine filler.
- Do not use Markdown tables. Do not create Markdown links; affiliate links are inserted separately.

ARTICLE TYPE
The user prompt supplies an intent-specific editorial job, structure, and must-cover list. Follow it. Do not force every article into the same heading sequence. A comparison, scenario, buyer guide, single-product review, alternatives article, and worth-it article must visibly feel different.

FACT BOUNDARY
The supplied product brief is the complete and exclusive source of product facts. Do not add specifications, features, compatibility, variants, accessories, prices, availability, awards, tests, reviews, rankings, or competitor claims not present in the brief. Reason from documented facts, but label inference and editorial judgement as such. Enrichment fields are verified editorial inputs; use the most relevant evidence rather than repeating every field.

ANTI-REPETITION
Do not mention every available fact. Select evidence that fits this article's decision criteria and evidence focus. Avoid repeating the same product fact in multiple sections unless it has a different practical consequence.

QUALITY
Target roughly 1,000-1,600 words where evidence supports it. A structurally complete article that contains generic category advice without product-specific reasoning is a failed article.

IMAGE PLANNING
Return 2-4 useful image_plan entries, exactly one hero. Each entry needs role, concept, search_query, alt_text and caption. Use lawful contextual Wikimedia Commons queries; never invent image URLs, licences, artists, or source claims.

OUTPUT
Return ONLY valid JSON with keys: title, slug, meta_description, body_markdown, products, image_plan. Selected products must preserve exact asin_or_id, price_range and key_points from the supplied brief.
"""

EDITOR_PROMPT = """Act as the senior editor receiving a first draft. Rewrite it into publication-quality decision content.

1. Remove generic introductions, filler, repeated points and AI boilerplate.
2. Make each major section answer a buyer question or explain a concrete consequence.
3. Strengthen the TechSignal judgement; do not hide behind neutrality.
4. Make trade-offs explicit.
5. Give useful buyer and skip conditions.
6. Follow the supplied intent-specific job and structure; do not impose a universal template.
7. Preserve only claims supported by the product brief.
8. Avoid repeating the same fact unless it serves a distinct decision consequence.
9. Keep 1,000-1,600 words when evidence supports it, without padding.
10. Return 2-4 image_plan entries with exactly one hero and lawful contextual search queries.

Return ONLY valid JSON with: title, slug, meta_description, body_markdown, products, image_plan.
"""

BANNED_OPENINGS = (
    "in today's world", "in todayÃ¢â‚¬â„¢s world", "whether you're", "whether youÃ¢â‚¬â„¢re",
    "if you're looking for", "if youÃ¢â‚¬â„¢re looking for", "choosing the right", "technology has become",
)


def load_topics() -> list[dict[str, Any]]:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    topics = data.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError("topics.json must contain a topics array")
    return expand_topics(topics, data.get("products", load_product_catalogue().get("products", [])))


def load_product_catalogue() -> dict[str, Any]:
    data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    products = data.get("products", [])
    if not isinstance(products, list) or not products:
        raise ValueError("products.json must contain a non-empty products array")
    return data


def _intent_key(topic: dict[str, Any]) -> str:
    raw = str(topic.get("intent", "buyer_guide")).strip().lower()
    if raw in {"buyer_guide", "comparison", "single_product_review", "scenario", "worth_it", "alternatives"}: return raw
    if "compar" in raw or raw in {"vs", "versus"}: return "comparison"
    if "scenario" in raw or "travel" in raw: return "scenario"
    if "worth" in raw: return "worth_it"
    if "alternative" in raw: return "alternatives"
    if "review" in raw: return "single_product_review"
    return "buyer_guide"

INTENT_GUIDANCE = {
    "buyer_guide": ("Help the reader choose what to buy for the stated need or budget.", "Start with the decision; identify the criteria that change the choice; test products against them; expose trade-offs; give a conditional verdict.", "decision criteria, practical consequences, buyer fit, skip conditions, verdict"),
    "comparison": ("Help the reader choose between the supplied products.", "Set decision criteria first; compare products against each criterion; explain meaningful differences and trade-offs; finish with winner-by-buyer conclusions.", "meaningful criteria, product-specific differences, trade-offs, buyer-specific winners"),
    "single_product_review": ("Determine whether one specific product makes sense for a particular buyer.", "Frame the use case; examine relevant strengths and limitations; explain practical consequences; give a qualified verdict.", "specific evidence, limitations, consequences, ideal buyer, reasons to skip"),
    "scenario": ("Solve a concrete technology decision in a realistic scenario.", "Open inside the scenario; identify the constraint; test relevant capabilities against it; surface compromises; make the decision explicit.", "scenario constraints, evidence tied to constraints, compromises, recommendation"),
    "worth_it": ("Answer whether a purchase is justified for the stated buyer.", "Define what worth-it means; weigh benefits against limitations and supported alternatives; make the value judgement explicit.", "value criteria, strongest buy reasons, strongest skip reasons, final judgement"),
    "alternatives": ("Help the reader choose an alternative when the obvious product is not the right fit.", "Explain why the default may fail; group alternatives by need; compare relevant differences; finish with fit-based recommendations.", "default failure modes, alternative evidence, trade-offs, buyer segmentation"),
}

def _editorial_brief(topic: dict[str, Any]) -> tuple[str, str, str]:
    return INTENT_GUIDANCE[_intent_key(topic)]

def _evidence_focus(topic: dict[str, Any], products: list[dict[str, Any]]) -> list[str]:
    pools=["detailed_specs","differentiators","known_limitations","who_its_for","who_should_skip"]
    seed=sum(ord(c) for c in str(topic.get("topic", ""))) + len(products)*17
    shift=seed % len(pools)
    return pools[shift:]+pools[:shift]

GENERIC_PHRASES=("in today's world","whether you're looking for","if you're looking for","choosing the right","the right choice","it is important to consider","when it comes to","there are many options","can be a great option","for many users","designed to meet","in conclusion","ultimately,")

def _quality_score(article: dict[str, Any], topic: dict[str, Any], product_brief: list[dict[str, Any]]) -> dict[str, Any]:
    body=str(article.get("body_markdown", "")); lower=body.lower(); words=re.findall(r"\b\w[\w'-]*\b",body)
    score=100; deductions=[]
    generic=sum(lower.count(x) for x in GENERIC_PHRASES)
    if generic>2: score-=min(20,(generic-2)*4); deductions.append(f"generic_phrases={generic}")
    if len(words)<700: score-=20; deductions.append("thin")
    if len(re.findall(r"^#{2,3}\s+.+$",body,re.M))<3: score-=8; deductions.append("few_headings")
    if not re.search(r"\b(recommend|recommendation|verdict|our take|should buy|should skip)\b",lower): score-=15; deductions.append("missing_verdict")
    trade=sum(lower.count(x) for x in ("trade-off","tradeoff","downside","limitation","compromise","give up"))
    if trade<2: score-=12; deductions.append("weak_tradeoffs")
    buyers=sum(lower.count(x) for x in ("best for","ideal for","who should","who should skip","not for","skip this"))
    if buyers<2: score-=10; deductions.append("weak_buyer_segmentation")
    matched=0
    for p in product_brief:
        terms=[str(p.get("name","")),*map(str,p.get("key_points",[])),*map(str,p.get("differentiators",[])),*map(str,p.get("known_limitations",[]))]
        matched+=sum(1 for t in terms if t and t.lower() in lower)
    if matched<4: score-=15; deductions.append(f"low_product_specificity={matched}")
    paras=[re.sub(r"\s+"," ",x.strip().lower()) for x in re.split(r"\n\s*\n",body) if x.strip()]
    dup=len(paras)-len(set(paras))
    if dup: score-=min(10,dup*5); deductions.append(f"duplicate_paragraphs={dup}")
    return {"score":max(0,score),"generic_hits":generic,"tradeoffs":trade,"buyer_hits":buyers,"deductions":deductions}

def build_product_brief(topic: dict[str, Any]) -> list[dict[str, Any]]:
    category = str(topic.get("category", "")).strip().lower()
    catalogue = load_product_catalogue()
    candidates = []
    for product in catalogue["products"]:
        if str(product.get("category", "")).lower() == category:
            candidates.append({
                "name": product.get("name"), "asin_or_id": product.get("asin_or_id"),
                "price_range": product.get("price_range"), "use_cases": product.get("use_cases", []),
                "key_points": product.get("key_points", []),
                "detailed_specs": product.get("detailed_specs", {}),
                "differentiators": product.get("differentiators", []),
                "known_limitations": product.get("known_limitations", []),
                "who_its_for": product.get("who_its_for", []),
                "who_should_skip": product.get("who_should_skip", []),
            })
    if not candidates:
        raise ValueError(f"No curated catalogue products match topic category: {category or 'unknown'}")
    return candidates[:6]


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("AI returned an empty response")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
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
    body=str(article.get("body_markdown", "")).strip(); plan=article.get("image_plan", [])
    if len(plan)<2 or len(plan)>4: raise ValueError("Editorial quality gate failed: image plan must contain 2-4 images")
    if sum(1 for x in plan if isinstance(x,dict) and str(x.get("role","")).lower()=="hero") != 1: raise ValueError("Editorial quality gate failed: exactly one hero image is required")
    for x in plan:
        if not isinstance(x,dict) or not all(str(x.get(k,"")).strip() for k in ("role","concept","search_query","alt_text")): raise ValueError("Editorial quality gate failed: image plan entry is incomplete")
    if body.lstrip("# ").lower().startswith(BANNED_OPENINGS): raise ValueError("Editorial quality gate failed: generic AI opening detected")
    allowed={str(p.get("asin_or_id")):p for p in product_brief}
    for selected in article.get("products",[]):
        asin=str(selected.get("asin_or_id",""))
        if asin not in allowed: raise ValueError(f"Editorial quality gate failed: product {asin or 'unknown'} is outside the supplied brief")
        for key in ("name","price_range","key_points"):
            if selected.get(key)!=allowed[asin].get(key): raise ValueError(f"Editorial quality gate failed: product field {key} was altered for {asin}")
    if _intent_key(topic)=="comparison" and len(product_brief)<2 and re.search(r"\b(vs\.?|versus|compared with|comparison)\b",body,re.I): raise ValueError("Editorial quality gate failed: unsupported product comparison")
    quality=_quality_score(article,topic,product_brief)
    if quality["score"]<72: raise ValueError(f"Editorial quality gate failed: substantive score {quality['score']}/100 ({', '.join(quality['deductions'])})")
    article["editorial_quality"]=quality


def _generate_editorial_draft(name: str, topic: dict[str, Any], product_brief: list[dict[str, Any]]) -> dict[str, Any]:
    job, structure, must_cover = _editorial_brief(topic)
    focus = _evidence_focus(topic, product_brief)
    prompt = f"""Write the first full editorial draft for this TechSignal topic.

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}
Editorial job: {job}
Editorial structure: {structure}
Must cover: {must_cover}
Evidence focus: {', '.join(focus)}

Allowed product brief (exclusive factual source):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Produce the complete article plus a 2-4 item image plan. Image search queries should target lawful contextual Wikimedia Commons imagery; never invent image URLs.
Return only the JSON object.
"""
    return _parse_json(generate_text(SYSTEM_PROMPT, prompt))


def _edit_draft(name: str, topic: dict[str, Any], product_brief: list[dict[str, Any]], draft: dict[str, Any]) -> dict[str, Any]:
    job, structure, must_cover = _editorial_brief(topic)
    focus = _evidence_focus(topic, product_brief)
    prompt = f"""Edit this TechSignal article to publication quality.

Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Category: {topic.get('category', 'general')}
Editorial job: {job}
Editorial structure: {structure}
Must cover: {must_cover}
Evidence focus: {', '.join(focus)}

Allowed product brief (exclusive factual source):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

FIRST DRAFT:
{json.dumps(draft, ensure_ascii=False, indent=2)}

{EDITOR_PROMPT}
"""
    return _parse_json(generate_text(SYSTEM_PROMPT, prompt))


def _slug(value: str) -> str:
    """Create a predictable WordPress-safe slug without depending on another module."""
    slug = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug[:100].strip("-") or "techsignal-article"


def generate_article(topic: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(topic, str):
        topic = {"topic": topic, "intent": "buyer_guide", "category": "general"}
    name = str(topic.get("topic", "")).strip()
    if not name:
        raise ValueError("Topic is empty")
    product_brief = build_product_brief(topic)
    draft = _generate_editorial_draft(name, topic, product_brief)
    try:
        article = _edit_draft(name, topic, product_brief, draft)
    except ValueError as edit_error:
        repair_prompt = f"""Return the following edited TechSignal article as valid JSON only.

Allowed product brief:
{json.dumps(product_brief, ensure_ascii=False, indent=2)}

Edited output:
{draft}

Required keys: title, slug, meta_description, body_markdown, products, image_plan.
Preserve substantive editorial analysis, but remove unsupported claims and invented products. Keep 2-4 image plan entries with one hero and lawful contextual Wikimedia Commons search queries.
"""
        try:
            article = _parse_json(generate_text(SYSTEM_PROMPT, repair_prompt))
        except ValueError as repair_error:
            raise ValueError(f"Editorial generation failed validation; edit error: {edit_error}; repair error: {repair_error}") from repair_error
    try:
        _validate_editorial_quality(article, product_brief, topic)
    except ValueError as quality_error:
        repair_prompt = f"""Rewrite this TechSignal article to fix the substantive editorial failure below.
Topic: {name}
Intent: {topic.get('intent', 'buyer_guide')}
Editorial job: {_editorial_brief(topic)[0]}
Editorial structure: {_editorial_brief(topic)[1]}
Evidence focus: {', '.join(_evidence_focus(topic, product_brief))}
Quality failure: {quality_error}
Allowed product brief (exclusive factual source):
{json.dumps(product_brief, ensure_ascii=False, indent=2)}
Current article:
{json.dumps(article, ensure_ascii=False, indent=2)}
Rewrite for concrete product-specific reasoning, explicit trade-offs, buyer/skip guidance and a clear verdict. Remove generic boilerplate. Do not invent facts. Return only the required JSON object."""
        article=_parse_json(generate_text(SYSTEM_PROMPT, repair_prompt))
        _validate_editorial_quality(article, product_brief, topic)
    article["slug"] = _slug(str(article.get("slug") or article["title"]))
    article["editorial_engine"] = "v3-external-images"
    article["editorial_passes"] = 2
    return article
