"""Adaptive daily publishing target based on durable quality and business signals."""
from __future__ import annotations
import json
from pathlib import Path

STATE = Path("data/scaling_state.json")
DEFAULT_TARGET = 5
TARGETS = (5, 7, 10)


def _bounded(value, low, high):
    return max(low, min(high, value))


def evaluate_metrics(metrics: dict) -> dict:
    """Move one level only when quality and demand evidence support it."""
    current = int(metrics.get("current_target", DEFAULT_TARGET))
    current = current if current in TARGETS else DEFAULT_TARGET
    quality = float(metrics.get("validation_pass_rate", 0))
    duplicate = float(metrics.get("duplicate_rejection_rate", 0))
    index_rate = float(metrics.get("index_rate", 0))
    affiliate = float(metrics.get("affiliate_click_rate", 0))
    traffic = float(metrics.get("traffic_7d_change", 0))
    if quality < 0.95 or duplicate > 0.35 or index_rate < 0.70:
        target = TARGETS[max(0, TARGETS.index(current) - 1)]
        reason = "quality, duplication, or indexing signal is below the scale gate"
    elif current < 10 and index_rate >= 0.85 and quality >= 0.98 and duplicate <= 0.20 and (affiliate > 0 or traffic > 0):
        target = TARGETS[TARGETS.index(current) + 1]
        reason = "quality, indexing, and demand signals support the next volume tier"
    else:
        target = current
        reason = "hold current tier until the next measurement window"
    return {"current_target": current, "recommended_target": target, "reason": reason, "metrics": metrics}


def load_state() -> dict:
    if not STATE.exists():
        return {"current_target": DEFAULT_TARGET}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"current_target": DEFAULT_TARGET}


def save_state(result: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(evaluate_metrics(load_state()), indent=2))
