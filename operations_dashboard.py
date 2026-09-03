"""Build an operational dashboard from GitHub Actions and local metrics."""
from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = os.getenv("GITHUB_REPOSITORY", "escapebusinesssolutions/news-ai-small-model")
WORKFLOW = "Small Model Publish"
API = "https://api.github.com"


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    return {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {token}"} if token else {})}


def fetch_runs(limit: int = 30) -> list[dict]:
    url = f"{API}/repos/{REPO}/actions/runs"
    r = requests.get(url, headers=_headers(), params={"per_page": limit}, timeout=30)
    r.raise_for_status()
    return [x for x in r.json().get("workflow_runs", []) if x.get("name") == WORKFLOW]


def load_json(path: str, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def build_dashboard() -> str:
    runs = fetch_runs()
    metrics = load_json("data/run_metrics.json", [])
    state = load_json("data/scaling_state.json", {"recommended_target": 5})
    repairs = load_json("data/repair_history.json", [])
    recent = runs[:20]
    completed = sum(1 for r in recent if r.get("status") == "completed")
    success = sum(1 for r in recent if r.get("conclusion") == "success")
    failed = sum(1 for r in recent if r.get("conclusion") == "failure")
    repaired = sum(1 for r in repairs[-50:] if r.get("result") == "repaired")
    rate = (success / completed * 100) if completed else 0.0
    target = int(state.get("recommended_target", state.get("current_target", 5)))
    rows = []
    for r in recent[:15]:
        status = r.get("conclusion") or r.get("status") or "unknown"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(r.get('created_at','')))}</td>"
            f"<td>{html.escape(str(r.get('event','')))}</td>"
            f"<td>{html.escape(status)}</td>"
            f"<td><a href='{html.escape(r.get('html_url',''), quote=True)}'>run</a></td>"
            "</tr>"
        )
    generated = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>TechSignal Operations Dashboard</title>
<meta name='description' content='TechSignal publishing operations dashboard.'>
<style>body{{font-family:system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 20px}}.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.card{{border:1px solid #ddd;border-radius:10px;padding:16px}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}.ok{{font-weight:700}}</style></head>
<body><h1>TechSignal Operations Dashboard</h1><p>Generated {html.escape(generated)} · target <strong>{target}/day</strong></p>
<div class='grid'><div class='card'><b>Runs</b><br>{len(recent)}</div><div class='card'><b>Completed</b><br>{completed}</div><div class='card'><b>Success rate</b><br>{rate:.1f}%</div><div class='card'><b>Failed</b><br>{failed}</div><div class='card'><b>Repaired</b><br>{repaired}</div></div>
<h2>Recent publication jobs</h2><table><thead><tr><th>Created</th><th>Trigger</th><th>Result</th><th>GitHub</th></tr></thead><tbody>{''.join(rows) or '<tr><td colspan="4">No runs found.</td></tr>'}</tbody></table>
<h2>Persistent metrics</h2><pre>{html.escape(json.dumps(metrics[-10:], indent=2))}</pre>
<h2>Current scale state</h2><pre>{html.escape(json.dumps(state, indent=2))}</pre>
<h2>Repair history</h2><pre>{html.escape(json.dumps(repairs[-20:], indent=2))}</pre>
</body></html>"""


def main() -> None:
    output = Path(os.getenv("OPERATIONS_DASHBOARD_PATH", "operations-dashboard.html"))
    output.write_text(build_dashboard(), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
