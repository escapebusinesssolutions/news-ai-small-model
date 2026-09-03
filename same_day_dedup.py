"""
Same-day topic dedup check.

Slots between M1 (story selection) and downstream generation/publish
stages. Purpose: at multi-run-per-day frequency, prevent the topic-index
selector from picking a story that's a near-duplicate of something
already published earlier the same UTC day.

Design constraints carried over from the project's governing rules:
- Converges into the canonical "story record" JSON schema rather than
  inventing a new bespoke shape (per news-ai-automation architecture rule).
- Fails closed: on ambiguity or missing data, treat as "skip and reselect"
  rather than risk publishing a near-duplicate.
- Bounded retries: never infinite-loop if the day's topic pool is thin.
- No paid infra: default comparison uses cheap lexical/entity overlap;
  the embedding-based path is optional and only used if the pipeline is
  already calling an embedding-capable API elsewhere (zero added cost).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 1. Story record schema addition
# ---------------------------------------------------------------------------
# Add these fields to the existing canonical story record JSON schema.
# Nothing here replaces existing fields — it's additive.
#
#   {
#     ...existing story record fields...,
#     "published_date": "2026-09-03",        # UTC date string, set on publish success
#     "topic_fingerprint": {
#         "keywords": ["openai", "gpt-6", "release"],
#         "entities": ["OpenAI"],
#         "embedding": null                   # optional, only if embeddings already in use
#     }
#   }


DEDUP_LOG_PATH = Path("data/published_today.json")  # committed rolling per-UTC-day record
MAX_RESELECTION_ATTEMPTS = 2
DEFAULT_SIMILARITY_THRESHOLD = 0.55  # tune after observing real false-positive rate

# Minimal stopword list for keyword extraction — replace with whatever
# tokenizer the pipeline already uses if one exists, to avoid a new dependency.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "at", "by", "as", "from", "that", "this",
}


@dataclass
class TopicFingerprint:
    keywords: set[str] = field(default_factory=set)
    entities: set[str] = field(default_factory=set)

    @classmethod
    def from_story_record(cls, record: dict) -> "TopicFingerprint":
        title = record.get("title", "")
        summary = record.get("summary", "")
        topic = record.get("topic", "")
        intent = record.get("intent", "")
        category = record.get("category", "")
        entities = set(record.get("entities", []))
        text = f"{title} {summary} {topic} {intent} {category}".lower()
        words = re.findall(r"[a-z0-9]+", text)
        keywords = {w for w in words if w not in _STOPWORDS and len(w) > 2}
        return cls(keywords=keywords, entities=entities)

    def similarity(self, other: "TopicFingerprint") -> float:
        """Jaccard overlap on keywords, boosted if entities overlap.
        Cheap, dependency-free, no API cost. Swap for embedding cosine
        distance later if the pipeline already has an embedding call
        elsewhere in the loop."""
        if not self.keywords or not other.keywords:
            kw_sim = 0.0
        else:
            intersection = len(self.keywords & other.keywords)
            union = len(self.keywords | other.keywords)
            kw_sim = intersection / union if union else 0.0

        entity_overlap = bool(self.entities & other.entities)
        if entity_overlap:
            kw_sim = min(1.0, kw_sim + 0.25)  # same named entity same day is a strong signal

        return kw_sim


def _today_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_todays_published_fingerprints() -> list[TopicFingerprint]:
    """Reads the rolling per-day record. Fails closed: if the file is
    missing, unreadable, or stale (not today's date), treat as empty —
    never block a run because the log itself is broken, but log loudly."""
    if not DEDUP_LOG_PATH.exists():
        return []
    try:
        data = json.loads(DEDUP_LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print(f"[dedup] WARNING: could not read {DEDUP_LOG_PATH}, treating as empty.")
        return []

    if data.get("date") != _today_utc_str():
        return []  # stale from a previous day — nothing published yet today

    return [
        TopicFingerprint(keywords=set(entry["keywords"]), entities=set(entry["entities"]))
        for entry in data.get("published", [])
    ]


def record_published_fingerprint(fingerprint: TopicFingerprint) -> None:
    """Call this only after a successful publish (post-M5), not before."""
    today = _today_utc_str()
    if DEDUP_LOG_PATH.exists():
        try:
            data = json.loads(DEDUP_LOG_PATH.read_text(encoding="utf-8"))
            if data.get("date") != today:
                data = {"date": today, "published": []}
        except (json.JSONDecodeError, OSError):
            data = {"date": today, "published": []}
    else:
        data = {"date": today, "published": []}

    data["published"].append({
        "keywords": sorted(fingerprint.keywords),
        "entities": sorted(fingerprint.entities),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })

    DEDUP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Write with explicit utf-8 per project rule; verify after write.
    DEDUP_LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    written = json.loads(DEDUP_LOG_PATH.read_text(encoding="utf-8"))
    assert written["published"][-1]["keywords"] == sorted(fingerprint.keywords), \
        "dedup log write verification failed"


def is_duplicate_of_today(
    candidate_record: dict,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[bool, Optional[float]]:
    """Returns (is_duplicate, max_similarity_found)."""
    candidate_fp = TopicFingerprint.from_story_record(candidate_record)
    todays = load_todays_published_fingerprints()
    if not todays:
        return False, None

    max_sim = max(candidate_fp.similarity(fp) for fp in todays)
    return max_sim >= threshold, max_sim


def select_non_duplicate_story(
    select_story_fn,
    max_attempts: int = MAX_RESELECTION_ATTEMPTS,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Optional[dict]:
    """
    Wraps the existing M1 story-selection function. `select_story_fn` should
    be a zero-arg callable returning a story record dict (i.e. partial-apply
    whatever topic-index logic already exists in automation_controller.py).

    Fails closed: if every attempt comes back a duplicate, returns None —
    the caller (automation_controller.py) should treat None as "skip this
    run, log clearly, do not publish" rather than force a duplicate through.
    """
    for attempt in range(1, max_attempts + 1):
        candidate = select_story_fn()
        is_dup, sim = is_duplicate_of_today(candidate, threshold=threshold)
        if not is_dup:
            if sim is not None:
                print(f"[dedup] Attempt {attempt}: accepted (max similarity {sim:.2f})")
            return candidate
        print(
            f"[dedup] Attempt {attempt}/{max_attempts}: rejected "
            f"'{candidate.get('title', '<untitled>')}' — similarity {sim:.2f} "
            f"exceeds threshold {threshold}"
        )

    print(f"[dedup] All {max_attempts} attempts exhausted — skipping this run's publish.")
    return None


def select_non_duplicate_topic(
    topics: list[dict],
    start_index: int,
    max_attempts: int = MAX_RESELECTION_ATTEMPTS,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[Optional[dict], Optional[int]]:
    """Select a topic, advancing through the catalogue when same-day dedup rejects it."""
    if not topics:
        return None, None
    attempts = min(max_attempts, len(topics))
    for offset in range(attempts):
        index = (start_index + offset) % len(topics)
        candidate = topics[index]
        is_dup, sim = is_duplicate_of_today(candidate, threshold=threshold)
        if not is_dup:
            print(f"[dedup] Topic index {index} accepted (max similarity {sim if sim is not None else 0:.2f})")
            return candidate, index
        print(f"[dedup] Topic index {index} rejected; similarity {sim:.2f} >= {threshold:.2f}")
    print(f"[dedup] No acceptable topic in {attempts} bounded attempts; skipping run.")
    return None, None


# ---------------------------------------------------------------------------
# Integration sketch for automation_controller.py (not wired in — reference only)
# ---------------------------------------------------------------------------
#
#   from same_day_dedup import select_non_duplicate_story, record_published_fingerprint, TopicFingerprint
#
#   if os.environ.get("ENABLE_SAME_DAY_DEDUP", "false").lower() == "true":
#       story = select_non_duplicate_story(lambda: run_m1_story_selection(...))
#       if story is None:
#           log_and_exit_cleanly("No non-duplicate topic available this run.")
#   else:
#       story = run_m1_story_selection(...)  # existing behavior, unchanged
#
#   ...existing M2-M5 pipeline runs on `story`...
#
#   if publish_succeeded:
#       record_published_fingerprint(TopicFingerprint.from_story_record(story))
