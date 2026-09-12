from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELECTOR = ROOT / "MACHINE-TS-V15-CONSUMER-SELECTOR-V01.py"
ACQUIRE = ROOT / "MACHINE-TS-V08-RIGHTS-AWARE-ACQUISITION-V01.py"
COMPOSITOR = ROOT / "MACHINE-TS-V16-CONSUMER-COMPOSITOR-V01.py"
QC = ROOT / "MACHINE-TS-V11-CONSUMER-QC-V01.py"


def stage(name, cmd, record):
    p = subprocess.run([str(x) for x in cmd], cwd=ROOT, capture_output=True, text=True)
    record.append({"stage": name, "exit_code": p.returncode,
                   "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]})
    if p.returncode:
        raise RuntimeError(f"{name}:{p.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    rd.mkdir(parents=True, exist_ok=True)
    stages = []
    try:
        selected = rd / "selector.json"
        stage("TS-V15-CONSUMER-SELECTOR", [sys.executable, SELECTOR,
              "--brief", args.brief, "--output", selected], stages)
        acquired_dir = rd / "acquired"
        acquired = rd / "acquired-manifest.json"
        stage("TS-V08-RIGHTS-AWARE-ASSET-ACQUISITION", [sys.executable, ACQUIRE,
              "--manifest", selected, "--output-dir", acquired_dir,
              "--output-manifest", acquired], stages)
        stage("TS-V16-CONSUMER-COMPOSITOR", [sys.executable, COMPOSITOR,
              "--manifest", acquired, "--voice", args.voice, "--output", args.output], stages)
        qc = rd / "visual-qc.json"
        stage("TS-V11-CONSUMER-VISUAL-QC", [sys.executable, QC,
              "--manifest", acquired, "--video", args.output, "--output", qc], stages)
        q = json.loads(qc.read_text(encoding="utf-8-sig"))
        if q.get("status") != "PASS":
            raise RuntimeError("TS-V11-CONSUMER-VISUAL-QC:REJECT")
        result = {"status": "PASS", "failure_code": None, "stages": stages,
                  "output": str(Path(args.output).resolve()), "visual_qc": q,
                  "portable_media": True, "source": "copied-from-large-model-m46"}
    except Exception as exc:
        result = {"status": "FAIL", "failure_code": str(exc), "stages": stages}
    (rd / "run-record.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
