from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def build_upload_metadata(video: Path, brief: Path) -> dict:
    data = json.loads(brief.read_text(encoding="utf-8-sig"))
    title = data.get("title") or data.get("product_name") or video.stem
    description = data.get("description") or data.get("script") or ""
    return {
        "video": str(video.resolve()),
        "title": str(title)[:100],
        "description": str(description),
        "privacyStatus": os.getenv("TECHSIGNAL_YOUTUBE_PRIVACY", "private"),
        "madeForKids": False,
        "channel_identity": "TECHSIGNAL_ONLY",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    video = Path(args.video).resolve()
    brief = Path(args.brief).resolve()
    if not video.is_file():
        raise SystemExit(f"video-not-found:{video}")
    if not brief.is_file():
        raise SystemExit(f"brief-not-found:{brief}")
    metadata = build_upload_metadata(video, brief)
    if not args.dry_run:
        raise SystemExit("TECHSIGNAL_YOUTUBE_UPLOAD_BLOCKED: dedicated OAuth credentials/channel not configured")
    Path(args.output).resolve().write_text(json.dumps({"status": "DRY_RUN", "metadata": metadata}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "DRY_RUN", "channel_identity": "TECHSIGNAL_ONLY", "video": str(video)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
