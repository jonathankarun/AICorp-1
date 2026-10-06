import json
from pathlib import Path

from backend.engine.demo_adapters import MockModelAdapter
from backend.engine.demo_models import AccessContext
from backend.engine.demo_pipeline import run_engine
from backend.engine.demo_repository import FixtureEvidenceRepository
from backend.engine.demo_retrieval import retrieve_query
from evaluation.retrieval_baseline import run_baseline

FIX = Path("tests/fixtures")


def load(name: str):
    return json.loads((FIX / name).read_text())


def test_12_query_retrieval_baseline_passes():
    result = run_baseline()
    assert result["answerable_top5"]["passed"] == result["answerable_top5"]["total"]
    assert result["answerable_top5"]["total"] == 9
    assert result["all_behavior_checks"]["passed"] == 12


def test_unrelated_request_returns_evidence_gap_before_model_call():
    adapter = MockModelAdapter(FIX / "mock_report.json")
    result = run_engine(load("assignment_no_evidence.json"), adapter)
    assert result.result_type == "evidence_gap"
    assert adapter.call_count == 0
    assert result.model_calls == 0


def test_forbidden_chunk_never_enters_model_context():
    adapter = MockModelAdapter(FIX / "mock_report.json")
    result = run_engine(load("assignment_forbidden.json"), adapter)
    assert result.result_type == "evidence_gap"
    assert adapter.call_count == 0
    assert "chunk-forbidden-001" in result.rejected_chunk_ids
    assert "chunk-forbidden-001" not in adapter.last_evidence_ids


def test_context_is_ranked_limited_and_source_aware():
    bundle = retrieve_query(
        "intake cycle time checklist triage cost",
        FixtureEvidenceRepository(),
        AccessContext(),
        max_chunks=3,
    )
    assert len(bundle.evidence) <= 3
    assert bundle.trace.context_word_count <= bundle.trace.max_context_words
    assert all(item.document_version_id for item in bundle.evidence)
    assert all(item.locator for item in bundle.evidence)


def test_first_chunk_cannot_exceed_context_budget():
    from backend.engine.demo_models import AccessContext, EvidenceChunk
    from backend.engine.demo_retrieval import _select_context

    oversized = EvidenceChunk(chunk_id="large", document_version_id="v1", title="Large",
                              source_uri="fixture://large", locator="page 1", text="word " * 11)
    small = oversized.model_copy(update={"chunk_id": "small", "text": "short evidence"})
    result = _select_context("evidence", [oversized, small], AccessContext(), max_context_words=10)
    assert [chunk.chunk_id for chunk in result.evidence] == ["small"]
    assert result.trace.context_word_count <= 10
