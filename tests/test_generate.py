import json

import pytest

import generate


def test_product_brief_uses_curated_catalogue():
    brief = generate.build_product_brief({"topic": "best microphones under $100", "category": "audio"})
    names = {item["name"] for item in brief}
    assert "Samson Q2U" in names
    assert "RØDE NT-USB Mini" in names
    assert all("asin_or_id" in item and "key_points" in item for item in brief)


def test_product_brief_rejects_queue_categories_without_catalogue_support():
    with pytest.raises(ValueError, match="No curated catalogue products"):
        generate.build_product_brief({"topic": "best keyboards under $100", "category": "keyboards"})


def test_generate_prompt_contains_product_brief_and_editorial_contract(monkeypatch):
    captured = {"calls": 0, "prompts": []}
    body = " ".join(["The practical buyer question is which trade-off matters most."] * 100)
    article = {
        "title": "Best microphones under $100",
        "body_markdown": body,
        "products": [{
            "name": "Samson Q2U",
            "asin_or_id": "B001R747SG",
            "price_range": "£30-£100",
            "key_points": ["USB/XLR dynamic microphone", "strong entry-level recording choice", "works for direct computer recording"],
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
    assert "Product brief" in captured["prompts"][0]
    assert "Samson Q2U" in captured["prompts"][0]
    assert "Samson Q2U" in captured["prompts"][1]
    assert "complete and exclusive source of product facts" in captured["system"]
    assert "Do not create Markdown links or Markdown tables" in captured["system"]
    assert "2-4 useful image_plan entries" in captured["system"]
    assert result["editorial_engine"] == "v3-external-images"
    assert result["editorial_passes"] == 2
    assert result["product_brief"]
