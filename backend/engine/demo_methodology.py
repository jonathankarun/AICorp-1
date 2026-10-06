from __future__ import annotations

from decimal import Decimal

from .demo_models import Assignment, CostEvidence, EvidenceChunk, EvidenceMapEntry
from .demo_repository import EvidenceRepository


METHODOLOGY_STAGES = [
    "clarify_problem",
    "identify_stakeholders_and_constraints",
    "retrieve_evidence",
    "compare_prior_work",
    "identify_gaps",
    "develop_alternatives",
    "assess_tradeoffs",
    "recommend_next_steps",
]

SECTION_HINTS = {
    "problem_summary": {"intake", "process", "cycle", "routing"},
    "findings": {"intake", "cycle", "routing", "duplicate", "timeline"},
    "alternatives": {"checklist", "triage", "intake"},
    "recommendation": {"checklist", "triage", "intake"},
    "implementation_steps": {"timeline", "checklist", "triage"},
    "risks": {"risk", "routing", "duplicate", "rework"},
    "cost_evidence": {"cost", "payment", "payments", "12000", "15000"},
    "sources": set(),
    "expert_review_needs": set(),
}


def _text_tokens(chunk: EvidenceChunk) -> set[str]:
    text = f"{chunk.title} {chunk.text}".lower()
    return {token.strip(".,:;()") for token in text.split()}


def build_evidence_map(
    assignment: Assignment,
    evidence: list[EvidenceChunk],
) -> list[EvidenceMapEntry]:
    entries: list[EvidenceMapEntry] = []
    for section in assignment.required_sections:
        hints = SECTION_HINTS.get(section, set())
        if hints:
            matches = [
                chunk.chunk_id for chunk in evidence if hints & _text_tokens(chunk)
            ]
        else:
            matches = [chunk.chunk_id for chunk in evidence[:2]]

        gap = not matches
        note = None
        if gap:
            note = f"No retrieved evidence directly supports required section '{section}'."
        entries.append(
            EvidenceMapEntry(
                section=section,
                supporting_chunk_ids=matches,
                gap=gap,
                notes=note,
            )
        )
    return entries


def calculate_cost_evidence(
    assignment: Assignment,
    repository: EvidenceRepository,
    query: str,
) -> CostEvidence:
    records = repository.get_historical_costs(query, assignment.department_id)
    if not records:
        return CostEvidence(
            min_amount=None,
            max_amount=None,
            currency="USD",
            fiscal_period=None,
            amount_type="actual_payment",
            source_ids=[],
            reason="No comparable historical cost evidence is available in the permitted fixture corpus.",
            limitation="No current cost estimate is inferred from missing evidence.",
        )

    amounts = [Decimal(record.amount) for record in records]
    currencies = {record.currency for record in records}
    periods = {record.fiscal_period for record in records}
    amount_types = {record.amount_type for record in records}
    source_ids = sorted({source for record in records for source in record.source_ids})

    return CostEvidence(
        min_amount=f"{min(amounts):.2f}",
        max_amount=f"{max(amounts):.2f}",
        currency=next(iter(currencies)) if len(currencies) == 1 else "USD",
        fiscal_period=next(iter(periods)) if len(periods) == 1 else "mixed",
        amount_type=next(iter(amount_types)) if len(amount_types) == 1 else "mixed",
        source_ids=source_ids,
        limitation=(
            "These are historical actual payments from fictional comparison records, not a current quote "
            "or authorized spending recommendation."
        ),
    )


def build_generation_context(
    assignment: Assignment,
    evidence: list[EvidenceChunk],
    repository: EvidenceRepository,
    query: str,
):
    evidence_map = build_evidence_map(assignment, evidence)
    cost_evidence = calculate_cost_evidence(assignment, repository, query)
    context = {
        "methodology_stages": METHODOLOGY_STAGES,
        "evidence_map": [entry.model_dump() for entry in evidence_map],
        "cost_evidence": cost_evidence.model_dump(),
    }
    return context, evidence_map, cost_evidence
