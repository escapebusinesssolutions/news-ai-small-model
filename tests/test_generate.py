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


def test_generate_prompt_contains_product_brief_and_decision_format(monkeypatch):
    captured = {}

    def fake_generate(system_prompt, prompt):
        captured["system"] = system_prompt
        captured["prompt"] = prompt
        return json.dumps({
            "title": "Best microphones under $100",
            "body_markdown": "Body",
            "products": [{"name": "Samson Q2U", "why_it_is_relevant": "Budget fit", "buying_note": "Good starting point"}],
        })

    monkeypatch.setattr(generate, "generate_text", fake_generate)
    result = generate.generate_article({"topic": "best microphones under $100", "category": "audio", "intent": "buyer_guide"})

    assert "Product brief" in captured["prompt"]
    assert "Samson Q2U" in captured["prompt"]
    assert "best X under Y" in captured["system"]
    assert result["product_brief"]
