"""Simple: This file proves that every required Jai validation-plan checkpoint passes and that the demo API exposes the same checks."""

from fastapi.testclient import TestClient

from backend.engine.final_demo_api import app
from evaluation.jai_final_validation import CASES, case_manifest, run_all, run_case, run_final_application_handoff


def test_every_required_validation_plan_case_passes():
    result = run_all()
    assert result["required_validation_cases"] == 12
    assert result["required_validation_passed"] == 12
    assert result["required_validation_complete"] is True


def test_all_demo_cases_include_longevity_bonus_and_pass():
    result = run_all()
    assert result["total_cases"] == 13
    assert result["failed_cases"] == 0


def test_manifest_maps_every_case_to_execution_and_validation_metadata():
    manifest = case_manifest()
    assert len(manifest) == 13
    assert len({item["case_id"] for item in manifest}) == 13
    for item in manifest:
        assert item["title"]
        assert item["execution_phase"]
        assert item["success_criteria"]
        assert item["methodology"]
        assert item["explanation"]
        assert item["technical_explanation"]


def test_usefulness_gate_can_fail_and_pass_live():
    failed = run_case(
        "VP-5.5",
        {"accuracy": 4.5, "completeness": 4.5, "usefulness": 3.0, "feasibility": 4.5},
    )
    assert failed["passed"] is False

    passed = run_case(
        "VP-5.5",
        {"accuracy": 4.5, "completeness": 4.5, "usefulness": 4.0, "feasibility": 4.5},
    )
    assert passed["passed"] is True


def test_controlled_failure_never_creates_a_new_report():
    result = run_case("VP-7.2")
    assert result["passed"] is True
    assert result["metrics"]["new_report_created_on_failure"] is False
    assert result["output"]["prior_report_still_available"] is True


def test_demo_api_manifest_and_single_step():
    client = TestClient(app)
    manifest = client.get("/api/demo/manifest")
    assert manifest.status_code == 200
    assert len(manifest.json()["cases"]) == 13

    step = client.post("/api/demo/run/VP-1.3", json={})
    assert step.status_code == 200
    assert step.json()["passed"] is True



def test_final_application_handoff_matches_shared_report_contract():
    payload = run_final_application_handoff()
    assert payload["status"] == "succeeded"
    report = payload["report_contract"]
    assert report["status"] == "draft"
    assert report["assignment_id"] == "jai-final-demo-001"
    assert {section["name"] for section in report["sections"]} >= {
        "findings", "alternatives", "recommendation", "implementation_steps", "risks"
    }
    assert payload["application_display"]["sources"]
    assert payload["application_display"]["quality_summary"]["section_coverage_pct"] == 100.0


def test_demo_api_final_handoff_route():
    client = TestClient(app)
    response = client.post("/api/demo/final-handoff", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["application_display"]["title"] == "AI Consulting Recommendation"

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# These tests are acceptance-level, not just unit tests. They require every
# validation-plan checkpoint to pass, verify the human-review gate can change
# state live, prove controlled failure preserves the prior report, and exercise
# the same FastAPI route used by the GUI. This prevents the presentation layer
# from drifting away from the underlying validation logic.
