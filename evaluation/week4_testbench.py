from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from backend.engine.week4_engine import EnginePolicy, MockProvider, run_week4_engine


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    return payload["cases"]


def _contains_case_insensitive(values: list[str], needle: str) -> bool:
    needle = needle.lower()
    return any(needle in value.lower() for value in values)


def evaluate_expected(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []

    for key in ("result_type", "code", "attempts", "provider_calls", "retryable", "uncertain_billing",
                "permission_change_from_source_text", "external_actions_authorized"):
        if key in expected and result.get(key) != expected[key]:
            failures.append(f"{key}: expected {expected[key]!r}, got {result.get(key)!r}")

    if "missing_field" in expected:
        if expected["missing_field"] not in result.get("missing_fields", []):
            failures.append(f"missing_fields did not contain {expected['missing_field']!r}")

    if len(result.get("injection_flags", [])) < expected.get("minimum_injection_flags", 0):
        failures.append("prompt-injection indicator was not captured")

    if len(result.get("conflicts", [])) < expected.get("minimum_conflicts", 0):
        failures.append("expected conflict was not surfaced")

    if "conflict_fact_key" in expected:
        conflicts = result.get("conflicts", [])
        match = next((c for c in conflicts if c.get("fact_key") == expected["conflict_fact_key"]), None)
        if match is None:
            failures.append(f"conflict fact_key {expected['conflict_fact_key']!r} not found")
        elif "conflict_values" in expected:
            actual_values = sorted(item["value"] for item in match.get("values", []))
            if actual_values != sorted(expected["conflict_values"]):
                failures.append(f"conflict values: expected {expected['conflict_values']}, got {actual_values}")

    if "report_expert_review_contains" in expected:
        report = result.get("report") or {}
        review = report.get("expert_review_needed", [])
        if not _contains_case_insensitive(review, expected["report_expert_review_contains"]):
            failures.append("expert-review indicator did not contain expected conflict note")

    revision = result.get("revision_trace", {})
    if "revision_of_report_id" in expected and revision.get("revision_of_report_id") != expected["revision_of_report_id"]:
        failures.append("revision_of_report_id was not preserved")
    if "prior_evidence_ids" in expected and revision.get("prior_evidence_ids_preserved") != expected["prior_evidence_ids"]:
        failures.append("prior evidence trace was not preserved")
    if "changed_requirement_contains" in expected:
        changed = revision.get("changed_requirements_reassessed", [])
        if not _contains_case_insensitive(changed, expected["changed_requirement_contains"]):
            failures.append("changed requirement was not recorded for reassessment")

    return not failures, failures


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    provider = MockProvider(
        behavior=case["provider"]["behavior"],
        response=case["provider"].get("response"),
    )
    policy = EnginePolicy.model_validate(case.get("policy", {}))
    result = run_week4_engine(case["assignment"], case["evidence"], provider, policy)
    passed, failures = evaluate_expected(result, case["expected"])
    return {
        "id": case["id"],
        "name": case["name"],
        "category": case["category"],
        "input_summary": {
            "assignment_id": case["assignment"]["assignment_id"],
            "problem": case["assignment"]["problem"],
            "evidence_chunk_ids": [item["chunk_id"] for item in case["evidence"]],
            "provider_behavior": case["provider"]["behavior"],
        },
        "expected": case["expected"],
        "actual": result,
        "passed": passed,
        "failures": failures,
    }


def build_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    category_counts = Counter(result["category"] for result in results)
    category_passes = Counter(result["category"] for result in results if result["passed"])

    false_success = 0
    bounded_attempts = True
    max_attempts = 0
    for result in results:
        expected_type = result["expected"].get("result_type")
        actual = result["actual"]
        if expected_type != "report" and actual.get("result_type") == "report":
            false_success += 1
        attempts = int(actual.get("attempts", 0))
        max_attempts = max(max_attempts, attempts)
        policy = actual.get("policy") or {}
        if policy and attempts > int(policy.get("max_attempts", attempts)):
            bounded_attempts = False

    by_category = {
        category: {
            "passed": category_passes[category],
            "total": category_counts[category],
            "fraction": category_passes[category] / category_counts[category],
        }
        for category in sorted(category_counts)
    }

    return {
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "false_success_count": false_success,
        "bounded_retry_policy_respected": bounded_attempts,
        "max_provider_attempts_observed": max_attempts,
        "by_category": by_category,
    }


def run_testbench(case_path: str | Path = "evaluation/week4_test_cases.json") -> dict[str, Any]:
    cases = load_cases(case_path)
    results = [run_case(case) for case in cases]
    return {"metrics": build_metrics(results), "results": results}


def print_console_summary(payload: dict[str, Any]) -> None:
    results = payload["results"]
    metrics = payload["metrics"]

    print("=" * 96)
    print("JAI WEEK 4 ENGINE TESTBENCH — ADVERSARIAL / FAILURE-HANDLING VALIDATION")
    print("=" * 96)
    print(f"{'CASE':<7} {'SCENARIO':<48} {'EXPECTED':<16} {'ACTUAL':<16} {'TRY':>3}  RESULT")
    print("-" * 96)
    for item in results:
        actual = item["actual"]
        expected = item["expected"].get("result_type", "-")
        actual_label = actual.get("result_type", "-")
        if actual_label == "error":
            actual_label = actual.get("code", "error")
        expected_label = expected
        if expected == "error":
            expected_label = item["expected"].get("code", "error")
        status = "PASS" if item["passed"] else "FAIL"
        print(
            f"{item['id']:<7} {item['name'][:48]:<48} {expected_label[:16]:<16} "
            f"{actual_label[:16]:<16} {actual.get('attempts', 0):>3}  {status}"
        )

    print("\nVALIDATION METRICS")
    print("-" * 96)
    print(f"Total cases:                    {metrics['total_cases']}")
    print(f"Passed cases:                   {metrics['passed_cases']}")
    print(f"Failed cases:                   {metrics['failed_cases']}")
    print(f"Pass rate:                      {metrics['pass_rate']:.1%}")
    print(f"False-success count:            {metrics['false_success_count']}")
    print(f"Retry policy respected:         {metrics['bounded_retry_policy_respected']}")
    print(f"Max provider attempts observed: {metrics['max_provider_attempts_observed']}")
    for category, values in metrics["by_category"].items():
        print(f"{category + ':':<32} {values['passed']}/{values['total']} ({values['fraction']:.1%})")

    print("\nSCREENSHOT-WORTHY EXAMPLE OUTPUTS")
    print("-" * 96)
    ids = {item["id"]: item for item in results}
    for case_id in ("W4-09", "W4-10", "W4-07", "W4-04"):
        item = ids[case_id]
        actual = item["actual"]
        print(f"\n{case_id} — {item['name']}")
        print(json.dumps({
            "result_type": actual.get("result_type"),
            "code": actual.get("code"),
            "attempts": actual.get("attempts"),
            "provider_calls": actual.get("provider_calls"),
            "injection_flags": actual.get("injection_flags", []),
            "conflicts": actual.get("conflicts", []),
            "retryable": actual.get("retryable"),
            "report_expert_review_needed": (actual.get("report") or {}).get("expert_review_needed", []),
        }, indent=2))


def write_markdown_summary(payload: dict[str, Any], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    metrics = payload["metrics"]
    lines = [
        "# Jai Week 4 Testbench Results",
        "",
        f"- Total cases: **{metrics['total_cases']}**",
        f"- Passed: **{metrics['passed_cases']}**",
        f"- Failed: **{metrics['failed_cases']}**",
        f"- Pass rate: **{metrics['pass_rate']:.1%}**",
        f"- False successes: **{metrics['false_success_count']}**",
        f"- Retry policy respected: **{metrics['bounded_retry_policy_respected']}**",
        f"- Max provider attempts observed: **{metrics['max_provider_attempts_observed']}**",
        "",
        "| Case | Scenario | Expected | Actual | Attempts | Result |",
        "|---|---|---|---|---:|---|",
    ]
    for item in payload["results"]:
        actual = item["actual"]
        expected = item["expected"].get("code", item["expected"].get("result_type", "-"))
        actual_label = actual.get("code", actual.get("result_type", "-"))
        lines.append(
            f"| {item['id']} | {item['name']} | {expected} | {actual_label} | "
            f"{actual.get('attempts', 0)} | {'PASS' if item['passed'] else 'FAIL'} |"
        )
    output.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jai Week 4 adversarial engine testbench")
    parser.add_argument("--cases", default="evaluation/week4_test_cases.json")
    parser.add_argument("--json-output", default="evidence/week-4/jai/testbench_results.json")
    parser.add_argument("--md-output", default="evidence/week-4/jai/testbench_summary.md")
    args = parser.parse_args()

    payload = run_testbench(args.cases)
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(payload, indent=2))
    write_markdown_summary(payload, args.md_output)
    print_console_summary(payload)
    print(f"\nWrote: {args.json_output}")
    print(f"Wrote: {args.md_output}")
    return 0 if payload["metrics"]["failed_cases"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
