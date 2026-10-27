"""Simple: This file shows that outdated AI models can be detected and replaced safely without editing engine code."""

from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from backend.engine.model_registry import (
    apply_approved_refreshes, load_fixture_catalog, load_registry,
    plan_refreshes, save_registry,
)

def run_testbench():
    registry = load_registry("config/model_registry.json")
    catalogs = load_fixture_catalog("evaluation/model_lifecycle_fixture.json")
    benchmark = json.loads(Path("evaluation/model_refresh_benchmark_fixture.json").read_text())
    today = date(2026, 10, 26)
    proposals = plan_refreshes(registry, catalogs, today=today)
    by_name = {p["name"]: p for p in proposals}
    updated, changes = apply_approved_refreshes(registry, proposals, benchmark, today=today)
    updated_by_name = {m["name"]: m for m in updated["models"]}

    checks = [
        ("ML-01", "Detect outdated OpenAI model", by_name["consulting_primary"]["needs_refresh"]),
        ("ML-02", "Choose approved OpenAI replacement", by_name["consulting_primary"]["replacement_model_id"] == "gpt-6-sol"),
        ("ML-03", "Detect outdated Anthropic model", by_name["consulting_secondary"]["needs_refresh"]),
        ("ML-04", "Choose approved Sonnet replacement", by_name["consulting_secondary"]["replacement_model_id"] == "claude-sonnet-5-5"),
        ("ML-05", "Require passed benchmark before update", len(changes) == 2),
        ("ML-06", "Update registry without engine-code edits",
            updated_by_name["consulting_primary"]["active_model_id"] == "gpt-6-sol"
            and updated_by_name["consulting_secondary"]["active_model_id"] == "claude-sonnet-5-5"),
        ("ML-07", "Keep old model in history for rollback",
            updated_by_name["consulting_primary"]["history"][0]["model_id"] == "gpt-5.1"),
    ]

    out = Path("evidence/model-lifecycle")
    out.mkdir(parents=True, exist_ok=True)
    save_registry(out / "proposed_model_registry.json", updated)
    result = {
        "total_cases": len(checks),
        "passed_cases": sum(bool(x[2]) for x in checks),
        "failed_cases": sum(not bool(x[2]) for x in checks),
        "checks": [{"id": i, "description": d, "passed": bool(p)} for i, d, p in checks],
        "changes": changes,
    }
    (out / "testbench_results.json").write_text(json.dumps(result, indent=2))
    return result

def main():
    r = run_testbench()
    print("AI CORPS - AUTOMATIC MODEL LONGEVITY TESTBENCH")
    print("=" * 80)
    print(f"Cases passed: {r['passed_cases']}/{r['total_cases']}")
    for c in r["checks"]:
        print(f"{c['id']}: {'PASS' if c['passed'] else 'FAIL'} - {c['description']}")
    print("\nPROPOSED CHANGES")
    for c in r["changes"]:
        print(f"{c['name']}: {c['old_model_id']} -> {c['new_model_id']}")
    print("\nResult: outdated model IDs can be refreshed through configuration instead of changing engine code.")
    return 0 if r["failed_cases"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())

# TECHNICAL EXPLANATION:
# The testbench exercises lifecycle detection, same-family replacement selection,
# benchmark gating, registry update, and migration history using deterministic
# fixtures. This makes the longevity logic demoable without provider API keys.
