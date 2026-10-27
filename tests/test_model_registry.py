"""Simple: This file checks that outdated models are detected and unsafe replacements are blocked."""

import json
from datetime import date
from backend.engine.model_registry import (
    ModelRecord, apply_approved_refreshes, choose_replacement, load_fixture_catalog,
    load_registry, needs_refresh, plan_refreshes,
)
from evaluation.model_lifecycle_testbench import run_testbench

def test_deprecated_model_requires_refresh():
    refresh, _ = needs_refresh(
        {"active_model_id": "old"},
        [ModelRecord("openai", "old", lifecycle="deprecated")],
        today=date(2026, 10, 26), warning_days=60,
    )
    assert refresh

def test_active_model_stays():
    refresh, _ = needs_refresh(
        {"active_model_id": "good"},
        [ModelRecord("openai", "good", lifecycle="active")],
        today=date(2026, 10, 26), warning_days=60,
    )
    assert not refresh

def test_replacement_stays_in_approved_family():
    entry = {"active_model_id": "old", "allowed_model_prefixes": ["gpt-6-sol"]}
    catalog = [
        ModelRecord("openai", "gpt-realtime-999", "active", "2026-12-01"),
        ModelRecord("openai", "gpt-6-sol", "active", "2026-10-01"),
    ]
    assert choose_replacement(entry, catalog).model_id == "gpt-6-sol"

def test_failed_benchmark_blocks_update():
    registry = {"models": [{
        "name": "primary", "provider": "openai", "active_model_id": "old",
        "allowed_model_prefixes": ["new"], "history": []
    }]}
    proposals = [{
        "name": "primary", "provider": "openai", "current_model_id": "old",
        "needs_refresh": True, "reason": "deprecated", "replacement_model_id": "new-v1"
    }]
    benchmark = {"candidates": [{"name": "primary", "model_id": "new-v1", "passed": False}]}
    updated, changes = apply_approved_refreshes(
        registry, proposals, benchmark, today=date(2026, 10, 26)
    )
    assert changes == []
    assert updated["models"][0]["active_model_id"] == "old"

def test_passed_benchmark_updates_and_keeps_history():
    registry = {"models": [{
        "name": "primary", "provider": "openai", "active_model_id": "old",
        "allowed_model_prefixes": ["new"], "history": []
    }]}
    proposals = [{
        "name": "primary", "provider": "openai", "current_model_id": "old",
        "needs_refresh": True, "reason": "deprecated", "replacement_model_id": "new-v1"
    }]
    benchmark = {"candidates": [{"name": "primary", "model_id": "new-v1", "passed": True}]}
    updated, changes = apply_approved_refreshes(
        registry, proposals, benchmark, today=date(2026, 10, 26)
    )
    assert len(changes) == 1
    assert updated["models"][0]["active_model_id"] == "new-v1"
    assert updated["models"][0]["history"][0]["model_id"] == "old"

def test_fixture_planner_finds_expected_replacements():
    registry = load_registry("config/model_registry.json")
    catalogs = load_fixture_catalog("evaluation/model_lifecycle_fixture.json")
    proposals = plan_refreshes(registry, catalogs, today=date(2026, 10, 26))
    found = {p["name"]: p["replacement_model_id"] for p in proposals}
    assert found["consulting_primary"] == "gpt-6-sol"
    assert found["consulting_secondary"] == "claude-sonnet-5-5"

def test_full_testbench_passes():
    result = run_testbench()
    assert result["passed_cases"] == 7
    assert result["failed_cases"] == 0

# TECHNICAL EXPLANATION:
# These tests protect the longevity guarantees: deprecated models trigger refresh,
# healthy models stay unchanged, replacement families are constrained, failed
# benchmarks cannot promote a model, passed migrations preserve history, and the
# full model-lifecycle testbench remains green.
