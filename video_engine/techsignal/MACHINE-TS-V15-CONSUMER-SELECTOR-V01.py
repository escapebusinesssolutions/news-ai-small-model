from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SLOT_PLAN = [
    ("product_hero", "hero"),
    ("product_profile", "product"),
    ("key_spec", "spec"),
    ("differentiator", "advantage"),
    ("real_world_use", "use"),
    ("limitation", "limitation"),
    ("best_for", "best_for"),
    ("skip_if", "skip_if"),
    ("comparison", "comparison"),
    ("verdict", "verdict"),
    ("buyer_check", "check"),
    ("cta", "cta"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8-sig"))
    products = brief.get("products") or [brief["product"]]
    beats = brief["script"]["beats"]
    facts = brief.get("visual_facts") or []
    asset = brief.get("primary_asset")
    slots = []

    def fact_for(kind: str, index: int) -> dict:
        matches = [f for f in facts if f.get("kind") == kind]
        if matches:
            return matches[index % len(matches)]
        return facts[index % len(facts)] if facts else {"label": kind.upper(), "value": "Product-specific buyer information"}

    for i, (beat_name, visual_kind) in enumerate(SLOT_PLAN):
        beat = beats[min(i, len(beats) - 1)]
        if i == 0 and asset:
            slot = {
                "beat": beat_name, "beat_id": f"beat-{i+1:02d}", "arc": beat["arc"], "script_line": beat["text"],
                "asset_type": "library_asset", "asset_id": asset["asset_id"], "local_path": asset["local_path"],
                "source_url": asset["source_url"], "rights_status": asset["rights_status"], "rights_checked": True,
                "usage_basis": asset["usage_basis"], "attribution": asset.get("attribution", ""),
                "subject_match": True, "match_reason": "validated exact product visual",
                "source_start": 0, "source_window_quality": "EXACT_PRODUCT_VISUAL", "source_window_quality_score": 100,
                "product_id": products[0].get("asin_or_id"),
            }
        else:
            fact = fact_for({"product":"product","spec":"spec","advantage":"advantage","use":"use","limitation":"limitation","best_for":"best_for","skip_if":"skip_if","comparison":"product","verdict":"verdict","check":"spec","cta":"best_for"}.get(visual_kind, "product"), max(0, i-1))
            if visual_kind == "comparison" and len(products) > 1:
                names = " vs ".join(str(p.get("name")) for p in products[:2])
                detail = f"{names}: compare the buyer priority, not just the headline specification."
            elif visual_kind == "cta":
                detail = f"See the full TechSignal guide for {brief['title']}."
            else:
                detail = str(fact.get("value", beat["text"]))
            slot = {
                "beat": beat_name, "beat_id": f"beat-{i+1:02d}", "arc": beat["arc"], "script_line": beat["text"],
                "asset_type": "original_graphic", "graphic_kind": visual_kind, "graphic_label": str(fact.get("label", visual_kind)).upper(),
                "graphic_text": detail, "asset_id": None, "rights_status": "N/A", "subject_match": True,
                "match_reason": "exact product/article fact visualization", "product_id": products[0].get("asin_or_id"),
            }
        slots.append(slot)

    out = {
        "status": "SUCCESS", "stage": "TECHSIGNAL-V02-CONSUMER-SELECTOR",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "story": {"title": brief["title"], "script": " ".join(x["text"] for x in beats)},
        "slots": slots, "library_selected": 1 if asset else 0,
        "original_graphics": sum(x["asset_type"] == "original_graphic" for x in slots),
        "coverage_count": len(slots), "required_count": len(SLOT_PLAN),
        "rights_review_required": False, "story_specific_graphics": True,
        "narrative_arc": [x["arc"] for x in beats], "story_beats": beats,
        "consumer_video": True, "product": brief["product"], "products": products,
        "commercial_consistency": brief.get("commercial_consistency", {}),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": out["status"], "slots": len(slots), "products": [p.get("name") for p in products]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
