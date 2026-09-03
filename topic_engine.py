"""Expand the curated topic seed into a larger, bounded buyer-intent catalogue."""
from __future__ import annotations

from typing import Any

ANGLES = {
    "audio": ["remote work calls", "home office", "podcasting", "voice clarity", "long work sessions", "small desk setups", "noise control", "travel work"],
    "storage": ["laptop backups", "large work files", "travel work", "limited laptop storage", "photo and video libraries", "fast file transfers", "portable work archives", "backup strategy"],
    "webcams": ["Zoom and Teams", "home office", "low-light meetings", "remote presentations", "compact desks", "client video calls", "camera upgrades", "video meeting quality"],
    "power": ["laptop travel", "mobile work", "airport work", "long workdays", "phone and laptop charging", "compact travel kits", "backup power", "business travel"],
    "workspace": ["fixed home offices", "small desks", "long work sessions", "productivity", "cable management", "laptop setups", "remote meetings", "desk upgrades"],
}

INTENTS = [
    ("buyer_guide", "best {category_label} for {angle}"),
    ("scenario", "best {category_label} when {angle}"),
    ("worth_it", "is upgrading your {category_label} worth it for {angle}"),
    ("alternatives", "best alternatives for {angle} when a basic {category_label} is not enough"),
]

LABELS = {"audio":"audio gear", "storage":"portable storage", "webcams":"webcams", "power":"charging and power gear", "workspace":"workspace gear"}


def expand_topics(seed: list[dict[str, Any]], products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep curated seeds first, then add deterministic angle variants not already present."""
    result = list(seed)
    seen = {str(x.get("topic", "")).strip().lower() for x in seed}
    categories = sorted({str(p.get("category", "")).lower() for p in products if p.get("category")})
    for category in categories:
        label = LABELS.get(category, f"{category} gear")
        for angle in ANGLES.get(category, []):
            for intent, template in INTENTS:
                topic = template.format(category_label=label, angle=angle)
                key = topic.lower()
                if key not in seen:
                    result.append({"topic": topic, "intent": intent, "category": category})
                    seen.add(key)
    # Comparisons are only generated where the catalogue has multiple products.
    for category in categories:
        names = [str(p.get("name")) for p in products if str(p.get("category", "")).lower() == category]
        if len(names) >= 2:
            for a, b in zip(names, names[1:]):
                topic = f"{a} vs {b}: which is better for practical work?"
                if topic.lower() not in seen:
                    result.append({"topic": topic, "intent": "comparison", "category": category})
                    seen.add(topic.lower())
    return result
