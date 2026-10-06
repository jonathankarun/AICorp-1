import json
from pathlib import Path

from backend.engine.demo_adapters import MockModelAdapter
from backend.engine.demo_methodology import METHODOLOGY_STAGES
from backend.engine.demo_pipeline import run_engine
from backend.engine.demo_repository import FixtureEvidenceRepository, NoCostFixtureRepository

FIX = Path("tests/fixtures")


def load(name: str):
    return json.loads((FIX / name).read_text())


def test_complete_source_backed_report_has_methodology_and_cost_range():
    adapter = MockModelAdapter(FIX / "mock_report_week3.json", prompt_version="v2")
    result = run_engine(
        load("assignment_week3_complete.json"),
        adapter,
        repository=FixtureEvidenceRepository(),
    )
    assert result.result_type == "report"
    assert result.usage.prompt_version == "v2"
    assert result.methodology_stages == METHODOLOGY_STAGES
    returned = {section.name for section in result.report.sections}
    assert set(load("assignment_week3_complete.json")["required_sections"]).issubset(returned)
    assert result.report.cost_evidence.min_amount == "12000.00"
    assert result.report.cost_evidence.max_amount == "15000.00"
    assert result.report.cost_evidence.amount_type == "actual_payment"
    valid = set(result.retrieval_trace.selected_chunk_ids)
    assert all(c.evidence_chunk_id in valid for c in result.report.citations)


def test_missing_cost_evidence_is_null_with_reason():
    adapter = MockModelAdapter(FIX / "mock_report_week3_no_cost.json", prompt_version="v2")
    result = run_engine(
        load("assignment_week3_complete.json"),
        adapter,
        repository=NoCostFixtureRepository(),
    )
    assert result.result_type == "report"
    assert result.report.cost_evidence.min_amount is None
    assert result.report.cost_evidence.max_amount is None
    assert result.report.cost_evidence.reason


def test_fake_citation_is_rejected():
    adapter = MockModelAdapter(FIX / "mock_report_week3_bad_citation.json", prompt_version="v2")
    result = run_engine(
        load("assignment_week3_complete.json"),
        adapter,
        repository=FixtureEvidenceRepository(),
    )
    assert result.result_type == "error"
    assert result.code == "invalid_model_output"
    assert "unknown evidence chunk" in result.message


def test_evidence_map_covers_requested_sections_or_marks_gap():
    adapter = MockModelAdapter(FIX / "mock_report_week3.json", prompt_version="v2")
    result = run_engine(load("assignment_week3_complete.json"), adapter)
    assert result.result_type == "report"
    mapped = {entry.section for entry in result.evidence_map}
    assert mapped == set(load("assignment_week3_complete.json")["required_sections"])
    assert all(entry.supporting_chunk_ids or entry.gap for entry in result.evidence_map)
