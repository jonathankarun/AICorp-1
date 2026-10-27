"""Simple: This file automatically checks that every important Week 5 feature works the way we expect."""

import json
from decimal import Decimal
from pathlib import Path

from backend.engine.week5_evaluation import (
    BudgetExceeded,
    BudgetLedger,
    ProviderRate,
    UsageRecord,
    canonical_fingerprint,
    compute_cost,
    deduplicate_evidence,
    estimate_input_tokens,
)
from evaluation.week5_runner import (
    budget_block_demo,
    load_manifest,
    run_comparison,
)


def test_cost_math_uses_declared_rate_units():
    rate = ProviderRate(
        model_id="fixture",
        rate_date="2026-10-25",
        rate_unit_tokens=1000,
        input_rate_usd=Decimal("0.002"),
        output_rate_usd=Decimal("0.008"),
    )
    usage = UsageRecord(
        model_id="fixture",
        input_tokens=1000,
        output_tokens=500,
        elapsed_ms=10,
    )
    assert compute_cost(usage, rate) == Decimal("0.006000")


def test_budget_reservation_is_atomic_and_blocks_overspend():
    ledger = BudgetLedger("0.010000")
    first = ledger.reserve(Decimal("0.007000"))
    try:
        ledger.reserve(Decimal("0.004000"))
    except BudgetExceeded:
        pass
    else:
        raise AssertionError("second reservation should have been blocked")
    ledger.cancel(first)


def test_duplicate_context_tuning_removes_only_repeated_text():
    manifest = load_manifest()
    before = estimate_input_tokens(manifest["assignment"], manifest["evidence"])
    after_evidence, removed = deduplicate_evidence(manifest["evidence"])
    after = estimate_input_tokens(manifest["assignment"], after_evidence)
    assert removed == ["w5-intake-1-duplicate"]
    assert len(after_evidence) == len(manifest["evidence"]) - 1
    assert after < before


def test_candidate_comparison_uses_equal_inputs_and_equal_run_counts():
    result = run_comparison(deduplicate_context=True)
    assert result["same_assignment_and_evidence"] is True
    assert result["equal_runs_per_candidate"] is True
    assert len({item["input_fingerprint"] for item in result["candidate_results"]}) == 1


def test_failed_candidate_run_is_recorded_not_hidden():
    result = run_comparison(deduplicate_context=True)
    low = next(
        item["summary"]
        for item in result["candidate_results"]
        if item["summary"]["candidate_id"] == "low_cost_candidate"
    )
    assert low["runs"] == 3
    assert low["failures"] == 1
    assert low["failure_codes"]["missing_required_sections"] == 1


def test_quality_gate_selects_stronger_fixture_candidate():
    result = run_comparison(deduplicate_context=True)
    selected = result["selected_candidate"]
    assert selected is not None
    assert selected["candidate_id"] == "stronger_candidate"
    assert selected["meets_quality_gate"] is True


def test_budget_failure_happens_before_provider_call():
    result = budget_block_demo()
    assert result["result"]["code"] == "budget_exceeded"
    assert result["provider_calls"] == 0
    assert result["actual_cost_usd"] == "0.000000"


def test_tuning_reduces_estimated_context_without_changing_candidate_count():
    baseline = run_comparison(deduplicate_context=False)
    tuned = run_comparison(deduplicate_context=True)
    assert tuned["tuning"]["estimated_tokens_saved"] > 0
    assert len(tuned["candidate_results"]) == len(baseline["candidate_results"]) == 2


def test_fixture_manifest_records_versions_rates_and_peer_review():
    manifest = load_manifest()
    assert manifest["corpus_version"]
    assert manifest["prompt_version"]
    assert manifest["retrieval_version"]
    assert manifest["rate_schedule_label"]
    for candidate in manifest["candidates"]:
        assert candidate["rate"]["rate_date"]
        assert candidate["rate"]["rate_unit_tokens"] == 1000
    for runs in manifest["runs"].values():
        assert all(run["reviewer"]["reviewer_type"] == "peer" for run in runs)


def test_accomplishment_testbench_covers_original_week5_plan():
    from evaluation.week5_testbench import run_testbench

    result = run_testbench()
    assert result["total_cases"] == 8
    assert result["failed_cases"] == 0
    assert result["passed_cases"] == 8
    assert result["selected_candidate"]["candidate_id"] == "stronger_candidate"

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# These tests validate deterministic cost math, atomic budget reservation, the
# measured context-deduplication change, equal comparison inputs/run counts,
# visible candidate failures, quality-gate selection, pre-call budget blocking,
# tuning behavior, version/rate/reviewer metadata, and the complete screenshot
# testbench. Together they protect the Week 5 evaluation logic from regressions
# without making live API calls.
