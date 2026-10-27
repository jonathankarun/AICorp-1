"""Simple: This file runs the Week 5 comparison, budget check, tuning test, and Week 4 regression checks."""

from __future__ import annotations

import json
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.engine.week4_engine import EnginePolicy, MockProvider, run_week4_engine
from backend.engine.week5_evaluation import (
    BudgetExceeded,
    BudgetLedger,
    ProviderRate,
    UsageRecord,
    canonical_fingerprint,
    choose_lowest_cost_passing,
    compute_cost,
    deduplicate_evidence,
    estimate_input_tokens,
    freeze_configuration,
    meets_quality_gate,
    reserve_maximum_cost,
    score_result,
)


def load_manifest(path: str | Path = "evaluation/week5_development_set.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _candidate_rate(candidate: dict[str, Any]) -> ProviderRate:
    return ProviderRate.from_dict(
        {
            "model_id": candidate["model_id"],
            **candidate["rate"],
        }
    )


def run_single(
    *,
    assignment: dict[str, Any],
    evidence: list[dict[str, Any]],
    candidate: dict[str, Any],
    run_fixture: dict[str, Any],
    ledger: BudgetLedger,
) -> dict[str, Any]:
    rate = _candidate_rate(candidate)
    input_estimate = estimate_input_tokens(
        assignment,
        evidence,
        prompt_overhead_tokens=int(candidate.get("prompt_overhead_tokens", 180)),
    )
    maximum = reserve_maximum_cost(
        input_token_estimate=input_estimate,
        output_token_cap=int(candidate["max_output_tokens"]),
        rate=rate,
        embedding_allowance_usd=Decimal(
            str(candidate.get("embedding_allowance_usd", "0"))
        ),
    )

    provider = MockProvider(
        behavior=run_fixture.get("provider_behavior", "success"),
        response=run_fixture.get("response"),
    )

    try:
        reservation_id = ledger.reserve(maximum)
    except BudgetExceeded as exc:
        return {
            "status": "budget_blocked",
            "result": {
                "result_type": "error",
                "code": "budget_exceeded",
                "message": str(exc),
                "report": None,
            },
            "provider_calls": provider.call_count,
            "reserved_maximum_cost_usd": f"{maximum:.6f}",
            "actual_cost_usd": "0.000000",
            "usage": None,
            "score": score_result(
                {"result_type": "error", "code": "budget_exceeded"},
                required_sections=assignment.get("required_sections", []),
                reviewer=run_fixture["reviewer"],
            ),
        }

    started = time.perf_counter()
    result = run_week4_engine(
        assignment,
        evidence,
        provider,
        policy=EnginePolicy(
            call_timeout_seconds=1.0,
            run_timeout_seconds=3.0,
            max_attempts=2,
            max_output_chars=20000,
        ),
    )
    local_engine_elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))

    # Week 5 fixture mode intentionally keeps provider-reported usage separate
    # from estimates. These numbers are controlled development data until a
    # real provider is authorized.
    usage = UsageRecord(
        model_id=candidate["model_id"],
        input_tokens=input_estimate,
        output_tokens=int(run_fixture["fixture_output_tokens"]),
        elapsed_ms=int(run_fixture["fixture_provider_elapsed_ms"]),
        retries=max(0, int(result.get("attempts", 1)) - 1),
        revisions=int(run_fixture.get("revisions", 0)),
        usage_source="fixture_estimate",
        billing_uncertain=bool(result.get("uncertain_billing", False)),
    )
    actual_cost = compute_cost(usage, rate)

    try:
        ledger.reconcile(reservation_id, actual_cost)
    except RuntimeError:
        # Preserve the real accounting problem as a failed result instead of
        # silently hiding it.
        result = {
            "result_type": "error",
            "code": "cost_reconciliation_error",
            "message": "Observed fixture cost exceeded its reservation.",
            "report": None,
        }

    score = score_result(
        result,
        required_sections=assignment.get("required_sections", []),
        reviewer=run_fixture["reviewer"],
    )
    return {
        "status": "completed" if result.get("result_type") == "report" else "failed",
        "result": result,
        "provider_calls": provider.call_count,
        "reserved_maximum_cost_usd": f"{maximum:.6f}",
        "actual_cost_usd": f"{actual_cost:.6f}",
        "usage": {
            "model_id": usage.model_id,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "elapsed_ms": usage.elapsed_ms,
            "local_engine_elapsed_ms": local_engine_elapsed_ms,
            "retries": usage.retries,
            "revisions": usage.revisions,
            "usage_source": usage.usage_source,
            "billing_uncertain": usage.billing_uncertain,
            "rate_date": rate.rate_date,
            "rate_unit_tokens": rate.rate_unit_tokens,
            "input_rate_usd": str(rate.input_rate_usd),
            "output_rate_usd": str(rate.output_rate_usd),
        },
        "score": score,
    }


def _summarize_candidate(
    candidate: dict[str, Any],
    run_results: list[dict[str, Any]],
    gate: dict[str, Any],
) -> dict[str, Any]:
    scores = [float(item["score"]["total_score"]) for item in run_results]
    costs = [Decimal(item["actual_cost_usd"]) for item in run_results]
    latencies = [
        int(item["usage"]["elapsed_ms"])
        for item in run_results
        if item.get("usage")
    ]
    failures = sum(item["result"].get("result_type") != "report" for item in run_results)
    critical = sum(
        int(item["score"]["critical_unsupported_claims"]) for item in run_results
    )
    coverage = [
        float(item["score"]["required_section_coverage_pct"]) for item in run_results
    ]

    summary = {
        "candidate_id": candidate["candidate_id"],
        "model_id": candidate["model_id"],
        "runs": len(run_results),
        "successes": len(run_results) - failures,
        "failures": failures,
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "minimum_required_section_coverage_pct": min(coverage) if coverage else 0.0,
        "critical_unsupported_claims": critical,
        "average_cost_usd": (
            f"{sum(costs, Decimal('0')) / Decimal(len(costs)):.6f}"
            if costs
            else "0.000000"
        ),
        "total_cost_usd": f"{sum(costs, Decimal('0')):.6f}",
        "average_latency_ms": (
            round(sum(latencies) / len(latencies), 1) if latencies else None
        ),
        "failure_codes": dict(
            Counter(
                item["result"].get("code")
                for item in run_results
                if item["result"].get("result_type") != "report"
            )
        ),
    }
    summary["meets_quality_gate"] = meets_quality_gate(summary, gate)
    return summary


def run_week4_regressions() -> dict[str, Any]:
    """Re-run the four Week 4 cases explicitly named by the Week 5 guide."""
    try:
        from evaluation.week4_testbench import load_cases, run_case
    except ImportError:
        return {
            "available": False,
            "passed": 0,
            "total": 4,
            "results": [],
            "note": "Week 4 testbench not found in this checkout.",
        }

    cases = {
        case["id"]: case
        for case in load_cases("evaluation/week4_test_cases.json")
    }
    ids = ["W4-02", "W4-04", "W4-09", "W4-10"]
    results = []
    for case_id in ids:
        outcome = run_case(cases[case_id])
        results.append(
            {
                "id": case_id,
                "passed": bool(outcome["passed"]),
                "failures": outcome["failures"],
            }
        )
    return {
        "available": True,
        "passed": sum(item["passed"] for item in results),
        "total": len(results),
        "results": results,
    }


def run_comparison(
    manifest_path: str | Path = "evaluation/week5_development_set.json",
    *,
    deduplicate_context: bool,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    assignment = manifest["assignment"]
    original_evidence = manifest["evidence"]
    if deduplicate_context:
        evidence, removed_ids = deduplicate_evidence(original_evidence)
    else:
        evidence, removed_ids = list(original_evidence), []

    fingerprint = canonical_fingerprint(assignment, evidence)
    before_tokens = estimate_input_tokens(assignment, original_evidence)
    after_tokens = estimate_input_tokens(assignment, evidence)

    ledger = BudgetLedger(manifest["team_allowance_usd"])
    candidate_results = []
    for candidate in manifest["candidates"]:
        runs = manifest["runs"][candidate["candidate_id"]]
        run_results = [
            run_single(
                assignment=assignment,
                evidence=evidence,
                candidate=candidate,
                run_fixture=run_fixture,
                ledger=ledger,
            )
            for run_fixture in runs
        ]
        summary = _summarize_candidate(
            candidate,
            run_results,
            manifest["quality_gate"],
        )
        candidate_results.append(
            {
                "candidate": candidate,
                "summary": summary,
                "runs": run_results,
                "input_fingerprint": fingerprint,
            }
        )

    selected = choose_lowest_cost_passing(
        [item["summary"] for item in candidate_results],
        manifest["quality_gate"],
    )

    return {
        "corpus_version": manifest["corpus_version"],
        "prompt_version": manifest["prompt_version"],
        "retrieval_version": manifest["retrieval_version"],
        "same_assignment_and_evidence": (
            len({item["input_fingerprint"] for item in candidate_results}) == 1
        ),
        "input_fingerprint": fingerprint,
        "equal_runs_per_candidate": (
            len({item["summary"]["runs"] for item in candidate_results}) == 1
        ),
        "candidate_results": candidate_results,
        "selected_candidate": selected,
        "budget": {
            "allowance_usd": str(manifest["team_allowance_usd"]),
            "spent_usd": f"{ledger.spent_usd:.6f}",
            "reserved_usd": f"{ledger.reserved_usd:.6f}",
            "remaining_usd": f"{ledger.remaining_usd:.6f}",
        },
        "tuning": {
            "deduplicate_context": deduplicate_context,
            "duplicates_removed": removed_ids,
            "estimated_input_tokens_before": before_tokens,
            "estimated_input_tokens_after": after_tokens,
            "estimated_tokens_saved": before_tokens - after_tokens,
        },
    }


def budget_block_demo(
    manifest_path: str | Path = "evaluation/week5_development_set.json",
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    candidate = manifest["candidates"][1]
    run_fixture = manifest["runs"][candidate["candidate_id"]][0]
    evidence, _ = deduplicate_evidence(manifest["evidence"])
    # Intentionally tiny allowance to prove the provider is never called.
    result = run_single(
        assignment=manifest["assignment"],
        evidence=evidence,
        candidate=candidate,
        run_fixture=run_fixture,
        ledger=BudgetLedger("0.000001"),
    )
    return result


def main() -> int:
    output_dir = Path("evidence/week-5/jai")
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = run_comparison(deduplicate_context=False)
    tuned = run_comparison(deduplicate_context=True)
    budget_demo = budget_block_demo()
    regressions = run_week4_regressions()

    selected = tuned["selected_candidate"]
    frozen = freeze_configuration(
        output_dir / "frozen_configuration.json",
        selected=selected,
        manifest=load_manifest(),
        tuning=tuned["tuning"],
    )

    payload = {
        "baseline": baseline,
        "tuned": tuned,
        "budget_block_demo": budget_demo,
        "week4_regressions": regressions,
        "frozen_configuration": frozen,
        "limitations": [
            "Candidate outputs, token counts, latency, and provider rates are controlled development fixtures.",
            "This validates Week 5 scoring, budgeting, tuning, and selection logic; it is not a live-provider quality claim.",
            "Replace fixture usage/rates with authorized provider-reported values before final live model selection.",
        ],
    }
    (output_dir / "week5_results.json").write_text(json.dumps(payload, indent=2))

    lines = []
    lines.append("JAI WEEK 5 - QUALITY / COST DEVELOPMENT EVALUATION")
    lines.append("=" * 75)
    lines.append(f"Same assignment/evidence: {tuned['same_assignment_and_evidence']}")
    lines.append(f"Equal runs per candidate: {tuned['equal_runs_per_candidate']}")
    lines.append(
        f"Context tuning: removed {len(tuned['tuning']['duplicates_removed'])} duplicate chunk(s), "
        f"saved {tuned['tuning']['estimated_tokens_saved']} estimated input token(s)"
    )
    lines.append("")
    lines.append(
        f"{'Candidate':<22} {'Success':<9} {'Avg score':<11} "
        f"{'Avg cost':<12} {'Latency':<10} {'Gate'}"
    )
    lines.append("-" * 75)
    for item in tuned["candidate_results"]:
        s = item["summary"]
        lines.append(
            f"{s['candidate_id']:<22} "
            f"{s['successes']}/{s['runs']:<7} "
            f"{s['average_score']:<11.2f} "
            f"${s['average_cost_usd']:<11} "
            f"{str(s['average_latency_ms']) + ' ms':<10} "
            f"{'PASS' if s['meets_quality_gate'] else 'FAIL'}"
        )
    lines.append("")
    if selected:
        lines.append(
            f"SELECTED CONFIGURATION: {selected['candidate_id']} "
            f"({selected['model_id']})"
        )
        lines.append(
            "Reason: lowest-cost tested candidate that met every configured quality gate."
        )
    else:
        lines.append("SELECTED CONFIGURATION: NONE - no candidate met the quality gate.")
    lines.append("")
    lines.append("BUDGET SAFETY CHECK")
    lines.append(f"  Result: {budget_demo['result']['code']}")
    lines.append(f"  Provider calls: {budget_demo['provider_calls']} (expected 0)")
    lines.append(
        f"  Reserved maximum requested: ${budget_demo['reserved_maximum_cost_usd']}"
    )
    lines.append("")
    lines.append("WEEK 4 REGRESSION CHECKS")
    if regressions["available"]:
        lines.append(
            f"  No-evidence / fake citation / injection / conflict: "
            f"{regressions['passed']}/{regressions['total']} passed"
        )
    else:
        lines.append("  Week 4 regression files are not available in this checkout.")
    lines.append("")
    lines.append(
        "LIMITATION: comparison uses controlled fixture candidates, usage, latency, and rates; "
        "it is not a live-provider claim."
    )
    rendered = "\n".join(lines)
    print(rendered)
    (output_dir / "week5_summary.txt").write_text(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This runner gives every candidate the same assignment/evidence fingerprint and
# the same number of runs, records failures instead of hiding them, reconciles
# reserved cost against actual fixture usage, aggregates quality/cost/latency,
# applies the configured quality gate, runs the measured deduplication tuning,
# replays key Week 4 safety cases, and writes the selected frozen configuration.
# The controlled fixtures make the comparison repeatable and auditable.
