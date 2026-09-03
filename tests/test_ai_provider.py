import json

import pytest

import reused.ai_provider as ai_provider


class FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {"choices": [{"message": {"content": json.dumps({"ok": True})}}]}


def test_openrouter_call_passes_configured_temperature():
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["payload"] = json
        return FakeResponse()

    result = ai_provider._openrouter_call(
        "system", "prompt", "test-model", "key", 0.85, post=fake_post
    )

    assert json.loads(result)["ok"] is True
    assert captured["payload"]["temperature"] == 0.85


def test_generate_text_reads_temperature_from_environment(monkeypatch):
    captured = {}

    def fake_call(system, prompt, model, key, temperature, post=None):
        captured["temperature"] = temperature
        return "{}"

    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("AI_TEMPERATURE", "0.75")
    monkeypatch.setattr(ai_provider, "_openrouter_call", fake_call)

    assert ai_provider.generate_text("system", "prompt") == "{}"
    assert captured["temperature"] == 0.75


def test_generate_text_rejects_invalid_temperature(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("AI_TEMPERATURE", "not-a-number")

    with pytest.raises(ai_provider.ProviderError, match="AI_TEMPERATURE"):
        ai_provider.generate_text("system", "prompt")
