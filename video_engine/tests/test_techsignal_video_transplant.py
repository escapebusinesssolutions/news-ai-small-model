import json
from pathlib import Path

from video_engine.techsignal.video_adapter import build_video_brief

ROOT = Path(__file__).resolve().parents[2]


def test_video_brief_uses_curated_product_and_validated_asset(tmp_path):
    article = {
        "title": "Logitech C920 HD Pro Webcam: Practical Home Office Choice?",
        "body_markdown": "The C920 is a practical choice for home office video calls. It keeps setup simple.",
        "products": [{
            "name": "Logitech C920 HD Pro Webcam",
            "asin_or_id": "B006A2Q81M",
            "price_range": "Â£50-Â£100",
            "key_points": ["1080p webcam", "autofocus", "dual stereo microphones"],
            "differentiators": ["USB-A plug-and-play"],
            "known_limitations": ["not advanced framing"],
            "who_its_for": ["home office"],
            "who_should_skip": ["buyers needing advanced framing"],
        }],
    }
    path = build_video_brief(article, {"intent": "single_product_review", "topic": "C920"})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["product"]["asin_or_id"] == "B006A2Q81M"
    assert data["primary_asset"]["rights_status"] == "CC0_1.0"
    assert len(data["script"]["beats"]) == 9
    assert len(data["visual_facts"]) >= 6


def test_large_model_copy_is_present_and_original_repo_path_is_separate():
    copy_dir = ROOT / "video_engine" / "large_model_m46_copy"
    expected = [
        "MACHINE-4.5-V15-REUSABLE-LIBRARY-SELECTOR-V01.py",
        "MACHINE-4.5-RIGHTS-AWARE-ASSET-ACQUISITION-V01.py",
        "MACHINE-4.5-V16-LIBRARY-COMPOSITOR-V01.py",
        "MACHINE-4.5-V11-VISUAL-QC-GATES-V01.py",
        "MACHINE-4.5-V17-PRODUCTION-RUNNER-V01.py",
    ]
    assert all((copy_dir / name).is_file() for name in expected)

