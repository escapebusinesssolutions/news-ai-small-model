from __future__ import annotations
import asyncio
from pathlib import Path
import edge_tts

VOICE = "en-GB-RyanNeural"


def generate_voice(brief_path: Path, output_path: Path) -> Path:
    import json
    brief = json.loads(brief_path.read_text(encoding="utf-8-sig"))
    beats = brief.get("script", {}).get("beats", [])
    text = " ".join(str(x.get("text", "")).strip() for x in beats if x.get("text"))
    if not text:
        raise ValueError("video brief contains no narration beats")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(edge_tts.Communicate(text, VOICE).save(str(output_path)))
    return output_path
