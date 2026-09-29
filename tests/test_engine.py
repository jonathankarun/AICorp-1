import json
from pathlib import Path

from backend.engine.adapters import MockModelAdapter
from backend.engine.pipeline import run_engine

FIX = Path("tests/fixtures")


def load(name: str):
    return json.loads((FIX / name).read_text())


def test_complete_assignment_returns_valid_draft_report():
    adapter = MockModelAdapter(FIX / "mock_report.json")
    result = run_engine(load("assignment_complete.json"), adapter)

    assert result.result_type == "report"
    assert result.report.status == "draft"
    assert result.report.assignment_id == "assignment-fixture-001"
    assert adapter.call_count == 1
    section_names = {section.name for section in result.report.sections}
    assert "problem_summary" in section_names
    assert "recommendation" in section_names
    assert "implementation_steps" in section_names


def test_invalid_model_output_returns_typed_error():
    adapter = MockModelAdapter(FIX / "mock_report_invalid.json")
    result = run_engine(load("assignment_complete.json"), adapter)

    assert result.result_type == "error"
    assert result.code == "invalid_model_output"
    assert "unknown evidence chunk" in result.message


def test_rfq_only_needs_input_before_model_call():
    adapter = MockModelAdapter(FIX / "mock_report.json")
    result = run_engine(load("assignment_rfq_only.json"), adapter)

    assert result.result_type == "needs_input"
    assert adapter.call_count == 0
    assert result.model_calls == 0
    assert "intended_result" in result.missing_fields
    assert any("result" in q.lower() for q in result.questions)
