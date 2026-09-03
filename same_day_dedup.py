"""Rolling historical topic deduplication for TechSignal."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEDUP_LOG_PATH = Path("data/published_history.json")
HISTORY_DAYS = 90
MAX_RESELECTION_ATTEMPTS = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.55
MAX_SAME_CATEGORY_PER_DAY = 3
MAX_SAME_INTENT_PER_DAY = 4
_STOPWORDS = {"the","a","an","and","or","of","to","in","on","for","with","is","are","was","were","at","by","as","from","that","this"}

@dataclass
class TopicFingerprint:
    keywords: set[str] = field(default_factory=set)
    entities: set[str] = field(default_factory=set)
    category: str = ""
    intent: str = ""
    topic: str = ""

    @classmethod
    def from_story_record(cls, record: dict) -> "TopicFingerprint":
        text = " ".join(str(record.get(k, "")) for k in ("title","summary","topic","intent","category")).lower()
        words = re.findall(r"[a-z0-9]+", text)
        keywords = {w for w in words if w not in _STOPWORDS and len(w) > 2}
        entities = {str(x).lower() for x in record.get("entities", []) if str(x).strip()}
        return cls(keywords, entities, str(record.get("category", "")).lower(), str(record.get("intent", "")).lower(), str(record.get("topic", "")).lower())

    def similarity(self, other: "TopicFingerprint") -> float:
        union = self.keywords | other.keywords
        score = len(self.keywords & other.keywords) / len(union) if union else 0.0
        if self.entities & other.entities:
            score = min(1.0, score + 0.25)
        return score


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_history() -> dict:
    if not DEDUP_LOG_PATH.exists():
        return {"schema_version":"2.0","published":[]}
    try:
        data = json.loads(DEDUP_LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Dedup history is unreadable: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("published", []), list):
        raise RuntimeError("Dedup history has an invalid schema")
    return data


def load_published_history(max_days: int = HISTORY_DAYS) -> list[TopicFingerprint]:
    data = _read_history()
    today = datetime.now(timezone.utc).date()
    result = []
    for entry in data["published"]:
        try:
            age = (today - datetime.fromisoformat(entry["recorded_at"]).date()).days
            if 0 <= age <= max_days:
                result.append(TopicFingerprint(set(entry.get("keywords", [])), set(entry.get("entities", [])), str(entry.get("category", "")), str(entry.get("intent", "")), str(entry.get("topic", ""))))
        except (KeyError, ValueError, TypeError):
            continue
    return result


def load_todays_published_fingerprints() -> list[TopicFingerprint]:
    return load_published_history(0)


def record_published_fingerprint(fingerprint: TopicFingerprint) -> None:
    data = _read_history()
    today = datetime.now(timezone.utc).date()
    kept = []
    for entry in data["published"]:
        try:
            if (today - datetime.fromisoformat(entry["recorded_at"]).date()).days <= HISTORY_DAYS:
                kept.append(entry)
        except (KeyError, ValueError, TypeError):
            continue
    kept.append({"keywords":sorted(fingerprint.keywords),"entities":sorted(fingerprint.entities),"recorded_at":datetime.now(timezone.utc).isoformat(),"category":getattr(fingerprint, "category", ""),"intent":getattr(fingerprint, "intent", ""),"topic":getattr(fingerprint, "topic", "")})
    data = {"schema_version":"2.0","retention_days":HISTORY_DAYS,"published":kept}
    DEDUP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEDUP_LOG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(DEDUP_LOG_PATH.read_text(encoding="utf-8"))


def is_duplicate(candidate_record: dict, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> tuple[bool, Optional[float]]:
    candidate = TopicFingerprint.from_story_record(candidate_record)
    history = load_published_history()
    if not history:
        return False, None
    maximum = max(candidate.similarity(previous) for previous in history)
    return maximum >= threshold, maximum


def is_duplicate_of_today(candidate_record: dict, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> tuple[bool, Optional[float]]:
    candidate = TopicFingerprint.from_story_record(candidate_record)
    history = load_todays_published_fingerprints()
    if not history:
        return False, None
    maximum = max(candidate.similarity(previous) for previous in history)
    return maximum >= threshold, maximum


def select_non_duplicate_topic(topics: list[dict], start_index: int, max_attempts: int = MAX_RESELECTION_ATTEMPTS, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> tuple[Optional[dict], Optional[int]]:
    if not topics:
        return None, None
    attempts = min(max_attempts, len(topics))
    today = load_todays_published_fingerprints()
    category_counts = {}
    intent_counts = {}
    for item in today:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
        intent_counts[item.intent] = intent_counts.get(item.intent, 0) + 1
    for offset in range(attempts):
        index = (start_index + offset) % len(topics)
        candidate = topics[index]
        category = str(candidate.get("category", "")).lower()
        intent = str(candidate.get("intent", "")).lower()
        if category_counts.get(category, 0) >= MAX_SAME_CATEGORY_PER_DAY:
            print(f"[dedup] Topic index {index} rejected; daily category cap reached for {category}")
            continue
        if intent_counts.get(intent, 0) >= MAX_SAME_INTENT_PER_DAY:
            print(f"[dedup] Topic index {index} rejected; daily intent cap reached for {intent}")
            continue
        duplicate, score = is_duplicate(candidate, threshold)
        if not duplicate:
            print(f"[dedup] Topic index {index} accepted; historical similarity {score if score is not None else 0:.2f}")
            return topics[index], index
        print(f"[dedup] Topic index {index} rejected; historical similarity {score:.2f} >= {threshold:.2f}")
    print(f"[dedup] No acceptable topic in {attempts} bounded attempts; skipping run.")
    return None, None


def select_non_duplicate_story(select_story_fn, max_attempts: int = MAX_RESELECTION_ATTEMPTS, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> Optional[dict]:
    for attempt in range(max_attempts):
        candidate = select_story_fn()
        duplicate, score = is_duplicate(candidate, threshold)
        if not duplicate:
            return candidate
        print(f"[dedup] Story attempt {attempt + 1}/{max_attempts} rejected; similarity {score:.2f}")
    return None
