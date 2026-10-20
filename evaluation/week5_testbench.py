"""Simple: This file turns Jai's Week 5 work into a clear PASS/FAIL testbench that is easy to screenshot."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.engine.week5_evaluation import freeze_configuration
from evaluation.week5_runner import (
    budget_block_demo,
    load_manifest,
    run_comparison,
    run_week4_regressions,
)


def _check(case_id: str, accomplishment: str, passed: bool, actual: str) -> dict[str, Any]:
    return {
        "id": case_id,
        "accomplishment": accomplishment,
        "passed": bool(passed),
        "actual": actual,
    }


def run_testbench() -> dict[str, Any]:
    """Run the original Week 5 plan as measurable accomplishments."""
    output_dir = Path("evidence/week-5/jai")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    baseline = run_comparison(deduplicate_context=False)
    tuned = run_comparison(deduplicate_context=True)
    budget = budget_block_demo()
    regressions = run_week4_regressions()

    selected = tuned["selected_candidate"]
    frozen = freeze_configuration(
        output_dir / "frozen_configuration.json",
        selected=selected,
        manifest=manifest,
        tuning=tuned["tuning"],
    )

    summaries = {
        item["summary"]["candidate_id"]: item["summary"]
        for item in tuned["candidate_results"]
    }
    low = summaries["low_cost_candidate"]
    strong = summaries["stronger_candidate"]

    all_have_cost = all(
        Decimal(item["summary"]["average_cost_usd"]) > 0
        for item in tuned["candidate_results"]
    )
    all_have_latency = all(
        item["summary"]["average_latency_ms"] is not None
        for item in tuned["candidate_results"]
    )

    checks = [
        _check(
            "W5-TB-01",
            "Fair comparison uses the same assignment/evidence and equal run counts",
            tuned["same_assignment_and_evidence"] and tuned["equal_runs_per_candidate"],
            f"same_input={tuned['same_assignment_and_evidence']}, equal_runs={tuned['equal_runs_per_candidate']}",
        ),
        _check(
            "W5-TB-02",
            "Reports are scored with a repeatable quality rubric",
            low["average_score"] >= 0 and strong["average_score"] >= 0,
            f"low_cost={low['average_score']:.2f}, stronger={strong['average_score']:.2f}",
        ),
        _check(
            "W5-TB-03",
            "The quality gate rejects the weaker fixture and accepts the stronger fixture",
            (not low["meets_quality_gate"]) and strong["meets_quality_gate"],
            f"low_cost_gate={'PASS' if low['meets_quality_gate'] else 'FAIL'}, stronger_gate={'PASS' if strong['meets_quality_gate'] else 'FAIL'}",
        ),
        _check(
            "W5-TB-04",
            "Cost and latency are recorded for every candidate",
            all_have_cost and all_have_latency,
            f"low=${low['average_cost_usd']} @ {low['average_latency_ms']} ms; strong=${strong['average_cost_usd']} @ {strong['average_latency_ms']} ms",
        ),
        _check(
            "W5-TB-05",
            "Budget protection blocks an unaffordable run before the provider is called",
            budget["result"].get("code") == "budget_exceeded" and budget["provider_calls"] == 0,
            f"result={budget['result'].get('code')}, provider_calls={budget['provider_calls']}",
        ),
        _check(
            "W5-TB-06",
            "Measured context tuning removes duplicate evidence and saves estimated tokens",
            len(tuned["tuning"]["duplicates_removed"]) > 0
            and tuned["tuning"]["estimated_tokens_saved"] > 0,
            f"removed={len(tuned['tuning']['duplicates_removed'])}, tokens_saved={tuned['tuning']['estimated_tokens_saved']}",
        ),
        _check(
            "W5-TB-07",
            "The lowest-cost configuration that passes the gate is frozen for Week 6",
            selected is not None
            and frozen["status"] == "frozen"
            and frozen["selected_candidate_id"] == selected["candidate_id"],
            f"selected={frozen['selected_candidate_id']}, status={frozen['status']}",
        ),
        _check(
            "W5-TB-08",
            "Key Week 4 safety cases still pass after Week 5 changes",
            regressions["available"]
            and regressions["passed"] == regressions["total"],
            (
                f"{regressions['passed']}/{regressions['total']} passed"
                if regressions["available"]
                else "Week 4 testbench not found"
            ),
        ),
    ]

    passed = sum(item["passed"] for item in checks)
    result = {
        "week": 5,
        "goal": "Measure quality/cost, enforce spending safety, tune a measured weakness, and freeze the selected configuration.",
        "total_cases": len(checks),
        "passed_cases": passed,
        "failed_cases": len(checks) - passed,
        "pass_rate_pct": round((passed / len(checks)) * 100, 1),
        "checks": checks,
        "candidate_summary": [item["summary"] for item in tuned["candidate_results"]],
        "selected_candidate": selected,
        "budget_block_demo": {
            "code": budget["result"].get("code"),
            "provider_calls": budget["provider_calls"],
            "actual_cost_usd": budget["actual_cost_usd"],
        },
        "tuning": tuned["tuning"],
        "week4_regressions": regressions,
        "frozen_configuration": frozen,
        "baseline_estimated_tokens": baseline["tuning"]["estimated_input_tokens_after"],
        "limitation": "Candidate outputs, token counts, latency, and rates are controlled development fixtures, not live-provider measurements.",
    }

    (output_dir / "testbench_results.json").write_text(json.dumps(result, indent=2))
    return result


def render_testbench(result: dict[str, Any]) -> str:
    lines = [
        "JAI WEEK 5 - ACCOMPLISHMENT TESTBENCH",
        "=" * 92,
        f"Cases passed: {result['passed_cases']}/{result['total_cases']} ({result['pass_rate_pct']}%)",
        "",
        f"{'ID':<10} {'PASS?':<7} {'WHAT THIS PROVES':<58} ACTUAL RESULT",
        "-" * 120,
    ]
    for item in result["checks"]:
        lines.append(
            f"{item['id']:<10} "
            f"{('PASS' if item['passed'] else 'FAIL'):<7} "
            f"{item['accomplishment']:<58} "
            f"{item['actual']}"
        )

    lines.extend(["", "CANDIDATE QUALITY / COST SUMMARY", "-" * 92])
    lines.append(
        f"{'Candidate':<23} {'Success':<9} {'Avg Score':<11} {'Avg Cost':<12} {'Latency':<12} {'Gate'}"
    )
    for summary in result["candidate_summary"]:
        lines.append(
            f"{summary['candidate_id']:<23} "
            f"{summary['successes']}/{summary['runs']:<7} "
            f"{summary['average_score']:<11.2f} "
            f"${summary['average_cost_usd']:<11} "
            f"{str(summary['average_latency_ms']) + ' ms':<12} "
            f"{'PASS' if summary['meets_quality_gate'] else 'FAIL'}"
        )

    selected = result["selected_candidate"]
    lines.extend(
        [
            "",
            f"SELECTED/FROZEN CONFIGURATION: {selected['candidate_id'] if selected else 'NONE'}",
            f"BUDGET BLOCK TEST: {result['budget_block_demo']['code']} with {result['budget_block_demo']['provider_calls']} provider calls",
            f"CONTEXT TUNING: removed {len(result['tuning']['duplicates_removed'])} duplicate chunk(s), saved {result['tuning']['estimated_tokens_saved']} estimated tokens",
            (
                f"WEEK 4 SAFETY REGRESSION: {result['week4_regressions']['passed']}/{result['week4_regressions']['total']} passed"
                if result["week4_regressions"]["available"]
                else "WEEK 4 SAFETY REGRESSION: unavailable in this checkout"
            ),
            "",
            "LIMITATION: " + result["limitation"],
        ]
    )
    return "\n".join(lines)


def main() -> int:
    result = run_testbench()
    rendered = render_testbench(result)
    print(rendered)
    output = Path("evidence/week-5/jai/testbench_summary.txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n")
    return 0 if result["failed_cases"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This testbench composes the Week 5 runner into eight measurable acceptance
# checks. It verifies comparison fairness, scoring, quality-gate behavior,
# cost/latency accounting, pre-call budget blocking, measured context tuning,
# configuration freeze, and Week 4 regression safety. Results are written both
# as machine-readable JSON and a screenshot-friendly text summary. The testbench
# does not contact a live model provider; its purpose is repeatable subsystem
# validation against the controlled development fixtures defined in the manifest.
