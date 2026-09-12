from __future__ import annotations
import argparse
import hashlib
import json
import mimetypes
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import time

ALLOWED = {"EDITORIAL_ALLOWED", "LOCAL_TEST_ONLY", "REPOSITORY_ASSET", "CC_BY_3.0"}
BLOCKED = {"REVIEW_REQUIRED", "DENIED", "UNKNOWN", None, ""}
UA = "EvolutionChannel/0.2 rights-aware asset acquisition"
MAX_BYTES = 50 * 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(value: str, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "").strip("._")
    return (s[:100] or fallback)


def download(url: str, target: Path) -> int:
    last_error = None
    for attempt in range(1, 4):
        req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            total = 0
            with urlopen(req, timeout=30) as r, target.open("wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise RuntimeError(f"asset exceeds {MAX_BYTES} bytes: {url}")
                    f.write(chunk)
            return total
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 3:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = max(5, int(retry_after)) if retry_after and str(retry_after).isdigit() else attempt * 10
            time.sleep(min(delay, 30))
    raise RuntimeError(f"asset download failed: {url}: {last_error}")


def validate_slot(slot: dict, index: int) -> None:
    if slot.get("asset_type") == "original_graphic":
        return
    status = slot.get("rights_status")
    if status in BLOCKED:
        raise RuntimeError(f"rights gate blocked slot {index}: {status}")
    if status not in ALLOWED and not str(status).startswith("CC_BY_"):
        raise RuntimeError(f"unknown rights status slot {index}: {status}")
    if status in {"LOCAL_TEST_ONLY", "REPOSITORY_ASSET"} or slot.get("local_path"):
        if not slot.get("local_path"):
            raise RuntimeError(f"local-test slot {index} has no local_path")
        return
    required = ("source_url", "usage_basis", "attribution_required", "rights_checked")
    missing = [k for k in required if slot.get(k) in (None, "")]
    if missing:
        raise RuntimeError(f"production rights metadata missing slot {index}: {','.join(missing)}")
    if slot.get("rights_checked") is not True:
        raise RuntimeError(f"production rights check not affirmed slot {index}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--output-manifest", required=True)
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    slots = manifest.get("slots") or []
    if not slots:
        raise RuntimeError("manifest has no slots")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    acquired = []
    for i, slot in enumerate(slots):
        validate_slot(slot, i)
        if slot.get("asset_type") == "original_graphic":
            acquired.append(dict(slot))
            continue
        item = dict(slot)
        status = slot.get("rights_status")
        if status in {"LOCAL_TEST_ONLY", "REPOSITORY_ASSET"} or slot.get("local_path"):
            src = Path(slot["local_path"])
            if not src.exists():
                raise RuntimeError(f"missing local test asset slot {i}: {src}")
            ext = src.suffix.lower() or ".bin"
            target = out_dir / f"slot-{i:02d}-{safe_name(slot.get('beat'), 'asset')}{ext}"
            shutil.copy2(src, target)
            size = target.stat().st_size
        else:
            url = slot["asset_url"]
            ext = Path(url.split("?", 1)[0]).suffix.lower()
            if not ext:
                ext = mimetypes.guess_extension(slot.get("mime_type", "")) or ".bin"
            target = out_dir / f"slot-{i:02d}-{safe_name(slot.get('beat'), 'asset')}{ext}"
            size = download(url, target)
        item.update({
            "local_path": str(target),
            "sha256": sha256(target),
            "bytes": size,
            "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        acquired.append(item)
    result = dict(manifest)
    result["stage"] = "M4.5-V08-RIGHTS-AWARE-ASSET-ACQUISITION-V01"
    result["acquired_slots"] = acquired
    result["acquisition_count"] = len(acquired)
    result["acquisition_policy"] = {
        "blocked_statuses": sorted(x for x in BLOCKED if x is not None),
        "production_requires_rights_metadata": True,
        "max_asset_bytes": MAX_BYTES,
    }
    Path(args.output_manifest).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({"status": "SUCCESS", "stage": result["stage"],
                      "acquired": len(acquired), "output_manifest": args.output_manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
