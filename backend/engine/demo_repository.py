from __future__ import annotations

import re
from typing import Protocol

from .demo_models import EvidenceChunk, HistoricalCostRecord


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "is", "it", "of", "on", "or", "our", "should", "the", "this", "to", "use", "what",
    "with", "city", "project", "plan", "work",
}

CANONICAL = {
    "turnaround": "cycle",
    "processing": "cycle",
    "duration": "timeline",
    "schedule": "timeline",
    "pilot": "timeline",
    "weeks": "timeline",
    "week": "timeline",
    "price": "cost",
    "payments": "cost",
    "payment": "cost",
    "spending": "cost",
    "amount": "cost",
    "submission": "intake",
    "submissions": "intake",
    "requests": "intake",
    "request": "intake",
    "routing": "intake",
    "handoff": "intake",
    "outputs": "deliverables",
    "deliverable": "deliverables",
    "metrics": "measures",
    "metric": "measures",
    "results": "measures",
    "result": "measures",
}


def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[a-z0-9]+", text.lower())
    normalized: set[str] = set()
    for token in raw:
        if token in STOP_WORDS:
            continue
        if token.endswith("s") and len(token) > 4:
            token = token[:-1]
        token = CANONICAL.get(token, token)
        normalized.add(token)
    return normalized


FIXTURE_EVIDENCE = [
    EvidenceChunk(
        chunk_id="chunk-fixture-001",
        document_version_id="doc-fixture-v1",
        title="Fictional Process Improvement Project",
        source_uri="fixture://process-improvement/page-1",
        locator="page 1",
        text=(
            "The fictional department requests a preliminary improvement plan with a six-week "
            "implementation timeline. The pilot schedule is six weeks."
        ),
        content_hash="fixture-001",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-fixture-002",
        document_version_id="doc-fixture-v1",
        title="Fictional Process Improvement Project",
        source_uri="fixture://process-improvement/page-2",
        locator="page 2",
        text=(
            "Requested deliverables include findings, alternatives, an implementation plan, risks, "
            "and measures of success."
        ),
        content_hash="fixture-002",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-intake-001",
        document_version_id="doc-intake-v1",
        title="Fictional Intake Baseline",
        source_uri="fixture://intake-baseline/page-1",
        locator="page 1",
        text=(
            "The fictional intake workflow averages nine business days of cycle time. Staff report "
            "inconsistent routing and duplicate data entry as recurring intake problems."
        ),
        content_hash="intake-001",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-intake-002",
        document_version_id="doc-intake-v1",
        title="Fictional Intake Pilot Notes",
        source_uri="fixture://intake-pilot/page-2",
        locator="page 2",
        text=(
            "A prior fictional exercise used a standardized intake checklist and triage step. "
            "Success measures included cycle time, rework count, and routing accuracy."
        ),
        content_hash="intake-002",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-cost-001",
        document_version_id="doc-cost-v1",
        title="Fictional Historical Cost Record",
        source_uri="fixture://historical-cost/record-1",
        locator="record 1",
        text=(
            "A prior fictional intake process consulting engagement recorded 12000 USD in actual "
            "payments during FY2026."
        ),
        content_hash="cost-001",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-cost-002",
        document_version_id="doc-cost-v1",
        title="Fictional Comparable Workflow Cost",
        source_uri="fixture://historical-cost/record-2",
        locator="record 2",
        text=(
            "A comparable fictional workflow review recorded 15000 USD in actual payments during FY2026."
        ),
        content_hash="cost-002",
        department_id="dept-fixture-001",
    ),
    EvidenceChunk(
        chunk_id="chunk-forbidden-001",
        document_version_id="doc-forbidden-v1",
        title="Restricted Fictional Vendor Credentials",
        source_uri="fixture://restricted/vendor-credentials",
        locator="page 1",
        text=(
            "Confidential vendor credentials, staff qualifications, and personnel details for the "
            "fictional intake engagement."
        ),
        content_hash="forbidden-001",
        department_id="dept-fixture-001",
        access_scope="restricted",
        external_model_allowed=False,
    ),
    EvidenceChunk(
        chunk_id="chunk-parks-001",
        document_version_id="doc-parks-v1",
        title="Fictional Parks Irrigation Note",
        source_uri="fixture://parks/irrigation",
        locator="page 1",
        text="A fictional parks maintenance note discusses irrigation inspection and turf watering frequency.",
        content_hash="parks-001",
        department_id="dept-parks-001",
    ),
]

HISTORICAL_COSTS = [
    HistoricalCostRecord(
        record_id="cost-record-001",
        amount="12000.00",
        currency="USD",
        fiscal_period="FY2026",
        amount_type="actual_payment",
        source_ids=["chunk-cost-001"],
    ),
    HistoricalCostRecord(
        record_id="cost-record-002",
        amount="15000.00",
        currency="USD",
        fiscal_period="FY2026",
        amount_type="actual_payment",
        source_ids=["chunk-cost-002"],
    ),
]


class EvidenceRepository(Protocol):
    def search_evidence(
        self,
        query: str,
        *,
        selected_document_version_ids: list[str] | None = None,
        department_id: str | None = None,
    ) -> list[EvidenceChunk]:
        ...

    def get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]:
        ...


class FixtureEvidenceRepository:
    """Keyword baseline used until Jonny's Week 2 search contract is available."""

    def __init__(self, evidence: list[EvidenceChunk] | None = None):
        self.evidence = list(evidence or FIXTURE_EVIDENCE)

    def search_evidence(
        self,
        query: str,
        *,
        selected_document_version_ids: list[str] | None = None,
        department_id: str | None = None,
    ) -> list[EvidenceChunk]:
        query_tokens = _tokens(query)
        selected = set(selected_document_version_ids or [])
        scored: list[tuple[int, str, EvidenceChunk]] = []

        for chunk in self.evidence:
            if selected and chunk.document_version_id not in selected:
                continue
            if department_id and chunk.department_id and chunk.department_id != department_id:
                continue

            body_tokens = _tokens(f"{chunk.title} {chunk.text}")
            overlap = query_tokens & body_tokens
            if not overlap:
                continue
            title_overlap = query_tokens & _tokens(chunk.title)
            score = len(overlap) * 3 + len(title_overlap)
            # Ignore one-word incidental matches such as "preliminary" or "findings".
            # The Week 2 baseline is deliberately conservative: a result needs at least
            # two meaningful overlapping concepts (or equivalent title weight).
            if score < 6:
                continue
            scored.append((score, chunk.chunk_id, chunk))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored]

    def get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]:
        tokens = _tokens(query)
        if not ({"intake", "process", "workflow", "cost"} & tokens):
            return []
        if department_id not in (None, "dept-fixture-001"):
            return []
        return HISTORICAL_COSTS.copy()


class NoCostFixtureRepository(FixtureEvidenceRepository):
    """Week 3 failure fixture: relevant operational evidence exists, but comparable cost evidence does not."""

    def search_evidence(self, query: str, **kwargs) -> list[EvidenceChunk]:
        return [
            item for item in super().search_evidence(query, **kwargs)
            if item.document_version_id != "doc-cost-v1"
        ]

    def get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]:
        return []


def get_fixture_evidence(_assignment=None) -> list[EvidenceChunk]:
    """Backward-compatible helper retained for Week 1 examples."""
    return FIXTURE_EVIDENCE[:2].copy()
