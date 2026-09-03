import json

import operations_dashboard
import repair_controller


def test_repair_classification_is_fail_closed():
    assert repair_controller.classify("HTTP 503 temporary failure") == "transient"
    assert repair_controller.classify("OpenRouter 429 rate limit") == "transient"
    assert repair_controller.classify("WordPress 403 forbidden") == "blocked"
    assert repair_controller.classify("pre-publish validation failed") == "blocked"
    assert repair_controller.classify("something unexpected happened") == "unknown"


def test_dashboard_renders_metrics(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operations_dashboard, "fetch_runs", lambda: [
        {"status": "completed", "conclusion": "success", "created_at": "2026-09-03T10:00:00Z", "event": "schedule", "html_url": "https://github.com/example/run/1"},
        {"status": "completed", "conclusion": "failure", "created_at": "2026-09-03T09:00:00Z", "event": "schedule", "html_url": "https://github.com/example/run/2"},
    ])
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "run_metrics.json").write_text(json.dumps([{"success": True}]), encoding="utf-8")
    (tmp_path / "data" / "scaling_state.json").write_text(json.dumps({"recommended_target": 5}), encoding="utf-8")
    (tmp_path / "data" / "repair_history.json").write_text(json.dumps([]), encoding="utf-8")
    html = operations_dashboard.build_dashboard()
    assert "TechSignal Operations Dashboard" in html
    assert "50.0%" in html
    assert "schedule" in html
