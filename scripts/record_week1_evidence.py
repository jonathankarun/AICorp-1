"""Record actual Week 1 checks; run with .venv/bin/python from any directory."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence/week-1/jonathan"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    manifest = {
        "owner": "Jonathan",
        "week": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": commit,
        "python_version": platform.python_version(),
        "fixture": "tests/fixtures/data_week1.json",
        "expected_results": "evidence/week-1/jonathan/expected_outputs.md",
        "commands": [],
    }
    commands = [
        (["-m", "pip", "check"], "dependencies.txt"),
        (["-m", "pytest", "--run-data", "-v"], "pytest.txt"),
        (["-m", "backend.data.validate", "--output", "evidence/week-1/jonathan/validation.json"], "validation-output.txt"),
    ]
    for arguments, filename in commands:
        started = time.monotonic()
        result = subprocess.run([sys.executable, *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (OUTPUT / filename).write_text(result.stdout)
        manifest["commands"].append({
            "command": ".venv/bin/python " + " ".join(arguments),
            "expected_exit_code": 0,
            "actual_exit_code": result.returncode,
            "passed": result.returncode == 0,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output": "evidence/week-1/jonathan/" + filename,
        })
        print(f"{filename}: {'PASS' if result.returncode == 0 else 'FAIL'}")
    manifest["passed"] = all(item["passed"] for item in manifest["commands"])
    (OUTPUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0 if manifest["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
