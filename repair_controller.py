"""Bounded, fail-closed repair controller for Small Model publishing."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO = os.getenv("GITHUB_REPOSITORY", "escapebusinesssolutions/news-ai-small-model")
API = "https://api.github.com"
WORKFLOW = "Small Model Publish"
HISTORY = Path("data/repair_history.json")
MAX_ATTEMPTS = 2
COOLDOWN_MINUTES = 20

SAFE_PATTERNS = (
    r"rate.?limit", r"429", r"timeout", r"timed out", r"connection reset", r"connection aborted",
    r"502", r"503", r"504", r"temporarily unavailable", r"temporary failure", r"runner.*lost",
    r"network", r"bad gateway", r"gateway timeout",
)
BLOCK_PATTERNS = (
    r"401", r"403", r"unauthorized", r"forbidden", r"authentication", r"permission denied",
    r"validation failed", r"pre-publish validation", r"duplicate", r"affiliate", r"unsupported marketplace",
)


def headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for repair control")
    return {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"}


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []


def save_history(rows: list[dict]) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(rows[-500:], indent=2) + "\n", encoding="utf-8")


def classify(text: str) -> str:
    lowered = text.lower()
    if any(re.search(p, lowered) for p in BLOCK_PATTERNS):
        return "blocked"
    if any(re.search(p, lowered) for p in SAFE_PATTERNS):
        return "transient"
    return "unknown"


def get_failed_runs() -> list[dict]:
    r = requests.get(f"{API}/repos/{REPO}/actions/runs", headers=headers(), params={"per_page": 30}, timeout=30)
    r.raise_for_status()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return [
        x for x in r.json().get("workflow_runs", [])
        if x.get("name") == WORKFLOW and x.get("conclusion") in {"failure", "cancelled"}
        and datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) >= cutoff
    ]


def job_logs(run_id: int) -> str:
    jobs = requests.get(f"{API}/repos/{REPO}/actions/runs/{run_id}/jobs", headers=headers(), params={"per_page": 100}, timeout=30)
    jobs.raise_for_status()
    text = []
    for job in jobs.json().get("jobs", []):
        if job.get("conclusion") not in {"failure", "cancelled"}:
            continue
        jr = requests.get(f"{API}/repos/{REPO}/actions/jobs/{job['id']}/logs", headers=headers(), timeout=30)
        if jr.ok:
            text.append(jr.text[-12000:])
        else:
            text.append(json.dumps(job))
    return "\n".join(text)


def repair_run(run: dict, history: list[dict]) -> dict:
    run_id = int(run["id"])
    prior = [x for x in history if x.get("run_id") == run_id]
    if len(prior) >= MAX_ATTEMPTS:
        return {"run_id": run_id, "result": "escalated", "reason": "repair attempt limit reached"}
    last = prior[-1] if prior else None
    if last and last.get("timestamp"):
        age = datetime.now(timezone.utc) - datetime.fromisoformat(last["timestamp"])
        if age < timedelta(minutes=COOLDOWN_MINUTES):
            return {"run_id": run_id, "result": "cooldown", "reason": "recent repair attempt"}
    classification = classify(job_logs(run_id))
    if classification != "transient":
        return {"run_id": run_id, "result": "escalated", "reason": f"failure classified as {classification}"}
    r = requests.post(f"{API}/repos/{REPO}/actions/runs/{run_id}/rerun-failed-jobs", headers=headers(), timeout=30)
    if r.status_code not in {201, 202}:
        return {"run_id": run_id, "result": "repair_failed", "reason": f"rerun API returned {r.status_code}"}
    return {"run_id": run_id, "result": "repaired", "classification": classification}


def main() -> None:
    history = load_history()
    results = []
    for run in get_failed_runs():
        result = repair_run(run, history)
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        history.append(result)
        results.append(result)
    save_history(history)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
