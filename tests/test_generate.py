import json

import pytest

import generate


def test_product_brief_uses_curated_catalogue():
    brief = generate.build_product_brief({"topic": "best microphones under $100", "category": "audio"})
    names = {item["name"] for item in brief}
    assert "Samson Q2U" in names
    assert any("NT-USB Mini" in name for name in names)
    assert all("asin_or_id" in item and "key_points" in item for item in brief)


def test_product_brief_rejects_queue_categories_without_catalogue_support():
    with pytest.raises(ValueError, match="No curated catalogue products"):
        generate.build_product_brief({"topic": "best keyboards under $100", "category": "keyboards"})


def test_generate_prompt_contains_product_brief_and_editorial_contract(monkeypatch):
    captured = {"calls": 0, "prompts": []}
    body = """## The decision

The Samson Q2U is a USB/XLR dynamic microphone, so the practical choice is whether that connection flexibility matters for this buyer.

## What you get

For a buyer who wants direct computer recording, the Q2U is a strong entry-level choice. The useful trade-off is between its straightforward USB path and the option to use XLR later.

## Who should buy it

This is best for a buyer who values USB/XLR flexibility and direct computer recording.

## Who should skip it

Skip it if those capabilities do not matter to your setup.

## Our verdict

TechSignal recommends the Q2U when USB/XLR flexibility is part of the buying decision; otherwise the buyer should compare the other supplied options.""" + " Additional buyer context with documented specifications and known limitations." * 220
    article = {
        "title": "Best microphones under $100",
        "body_markdown": body,
        "products": [{
            "name": "Samson Q2U",
            "asin_or_id": "B001R747SG",
            "price_range": generate.build_product_brief({"topic": "best microphones under $100", "category": "audio"})[0]["price_range"],
            "key_points": generate.build_product_brief({"topic": "best microphones under $100", "category": "audio"})[0]["key_points"],
        }],
        "image_plan": [
            {"role": "hero", "concept": "desk microphone recording setup", "search_query": "desktop microphone recording", "alt_text": "Microphone on a desk beside a computer", "caption": "A desktop recording setup."},
            {"role": "context", "concept": "person speaking into desk microphone", "search_query": "person speaking microphone desk", "alt_text": "Person speaking into a microphone at a desk", "caption": "A typical voice recording setup."},
        ],
    }

    def fake_generate(system_prompt, prompt):
        captured["calls"] += 1
        captured["prompts"].append(prompt)
        captured["system"] = system_prompt
        return json.dumps(article)

    monkeypatch.setattr(generate, "generate_text", fake_generate)
    result = generate.generate_article({"topic": "best microphones under $100", "category": "audio", "intent": "buyer_guide"})

    assert captured["calls"] == 2
    assert "Allowed product brief" in captured["prompts"][0]
    assert "Samson Q2U" in captured["prompts"][0]
    assert "Samson Q2U" in captured["prompts"][1]
    assert "complete and exclusive source of product facts" in captured["system"]
    assert "Do not use Markdown tables" in captured["system"]
    assert "Do not create Markdown links" in captured["system"]
    assert "2-4 useful image_plan entries" in captured["system"]
    assert "intent-specific" in captured["system"]
    assert "Editorial job:" in captured["prompts"][0]
    assert "Evidence focus:" in captured["prompts"][0]
    assert result["editorial_quality"]["score"] >= 72
    assert result["editorial_engine"] == "v3-external-images"
    assert result["editorial_passes"] == 2


def test_quality_gate_rejects_generic_article():
    product = generate.build_product_brief({"topic": "best microphones under $100", "category": "audio"})
    article = {"title": "Generic", "body_markdown": "The practical buyer question is which trade-off matters most. " * 180, "products": [{"name": product[0]["name"], "asin_or_id": product[0]["asin_or_id"], "price_range": product[0]["price_range"], "key_points": product[0]["key_points"]}], "image_plan": [{"role": "hero", "concept": "microphone desk", "search_query": "desktop microphone recording", "alt_text": "Microphone on a desk", "caption": "A desktop microphone setup."}, {"role": "context", "concept": "recording", "search_query": "person speaking microphone", "alt_text": "Person speaking into a microphone", "caption": "Voice recording context."}]}
    with pytest.raises(ValueError, match="substantive score"):
        generate._validate_editorial_quality(article, product, {"intent": "buyer_guide", "category": "audio"})


def test_intent_guidance_changes_by_article_type():
    buyer = generate._editorial_brief({"intent": "buyer_guide"})
    comparison = generate._editorial_brief({"intent": "comparison"})
    scenario = generate._editorial_brief({"intent": "scenario"})
    assert buyer != comparison and comparison != scenario
    assert "criteria" in comparison[1].lower()
    assert "scenario" in scenario[0].lower()
