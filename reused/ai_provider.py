"""Provider abstraction for resilient M2 text generation."""
from __future__ import annotations

import os
from typing import Callable

import requests
from dotenv import load_dotenv

load_dotenv()

HF_URL = "https://router.huggingface.co/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_FREE_FALLBACK_MODELS = (
    "minimax/minimax-m2.7:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "inclusionai/ling-3.0-flash-fin:free",
)

class ProviderError(RuntimeError):
    """Raised when configured AI providers cannot generate a response."""

def _env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ProviderError(f"{name} is unavailable")
    return value

def _hf_call(system: str, prompt: str, model: str, token: str,
             post: Callable | None = None) -> str:
    post = post or requests.post
    payload = {"model": model, "input": [
        {"role": "system", "content": [{"type": "input_text", "text": system}]},
        {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
    ]}
    response = post(HF_URL, headers={"Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json"},
                    json=payload, timeout=120)
    if response.status_code != 200:
        raise ProviderError(f"HF HTTP {response.status_code}: {response.text[:1000]}")
    data = response.json()
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"].strip()
    texts = [block["text"] for item in data.get("output", [])
             if isinstance(item, dict) for block in item.get("content", [])
             if isinstance(block, dict) and isinstance(block.get("text"), str)]
    if texts and texts[-1].strip():
        return texts[-1].strip()
    raise ProviderError("HF response contained no text")

def _openrouter_call(system: str, prompt: str, model: str, key: str,
                     post: Callable | None = None) -> str:
    post = post or requests.post
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://escapebusinesssolutions.com", "X-Title": "News AI Automation"}
    models = [model] if model == DEFAULT_OPENROUTER_MODEL else [model]
    if model == DEFAULT_OPENROUTER_MODEL:
        models.extend(OPENROUTER_FREE_FALLBACK_MODELS)
    failures = []
    for candidate in models:
        payload = {"model": candidate, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]}
        try:
            response = post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            failures.append(f"{candidate}: network {type(exc).__name__}: {exc}")
            continue
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices and isinstance(choices[0], dict):
                content = choices[0].get("message", {}).get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            failures.append(f"{candidate}: no text")
            continue
        failures.append(f"{candidate}: HTTP {response.status_code} {response.text[:300]}")
        if response.status_code not in (404, 408, 409, 429, 500, 502, 503, 504):
            break
    detail = "; ".join(failures)
    raise ProviderError(f"OpenRouter free generation unavailable: {detail}")

def generate_text(system: str, prompt: str) -> str:
    """Generate text with explicit provider selection or bounded HF->OpenRouter fallback."""
    provider = os.getenv("AI_PROVIDER", "auto").strip().lower() or "auto"
    configured_model = os.getenv("AI_MODEL", "").strip()
    model = configured_model or DEFAULT_MODEL
    openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip() or DEFAULT_OPENROUTER_MODEL
    if provider == "openrouter":
        return _openrouter_call(system, prompt, configured_model or openrouter_model, _env("OPENROUTER_API_KEY"))
    if provider == "huggingface":
        return _hf_call(system, prompt, model, _env("HF_TOKEN"))
    if provider != "auto":
        raise ProviderError(f"Unsupported AI_PROVIDER: {provider}")
    try:
        hf_token = _env("HF_TOKEN")
        return _hf_call(system, prompt, model, hf_token)
    except ProviderError as hf_error:
        # Auto mode falls back when HF credentials are absent, quota is exhausted,
        # rate/server errors occur, or HF returns an unusable empty response.
        message = str(hf_error)
        retryable = any(f"HF HTTP {code}" in message for code in (402, 410, 429, 500, 502, 503, 504)) or "model_no_longer_supported" in message
        unusable = "HF response contained no text" in message
        if not (retryable or unusable):
            raise
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise ProviderError(f"HF unavailable and OPENROUTER_API_KEY is unavailable: {message}")
        return _openrouter_call(system, prompt, openrouter_model, key)
