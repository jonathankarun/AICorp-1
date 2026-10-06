from __future__ import annotations

from pydantic import ValidationError

from .demo_adapters import ModelAdapter
from .demo_methodology import build_generation_context, METHODOLOGY_STAGES
from .demo_models import (
    AccessContext,
    Assignment,
    EngineEvidenceGap,
    EngineFailure,
    EngineNeedsInput,
    EngineResult,
    EngineSuccess,
    Report,
)
from .demo_repository import EvidenceRepository, FixtureEvidenceRepository
from .demo_retrieval import retrieve_for_assignment
from .demo_scope import check_scope


def validate_assignment(data: dict | Assignment) -> Assignment:
    return data if isinstance(data, Assignment) else Assignment.model_validate(data)


def validate_report(
    raw_report: dict,
    valid_evidence_ids: set[str],
    required_sections: list[str] | None = None,
) -> Report:
    report = Report.model_validate(raw_report)

    for citation in report.citations:
        if citation.evidence_chunk_id not in valid_evidence_ids:
            raise ValueError(
                f"citation '{citation.citation_id}' points to unknown evidence chunk "
                f"'{citation.evidence_chunk_id}'"
            )

    if required_sections:
        returned = {section.name for section in report.sections}
        missing = [name for name in required_sections if name not in returned]
        if missing:
            raise ValueError(f"report is missing required sections: {missing}")
    return report


def run_engine(
    data: dict | Assignment,
    model_client: ModelAdapter,
    repository: EvidenceRepository | None = None,
    access_context: AccessContext | None = None,
    *,
    max_chunks: int = 5,
    max_context_words: int = 450,
) -> EngineResult:
    try:
        assignment = validate_assignment(data)
    except ValidationError as exc:
        return EngineFailure(code="invalid_assignment", message=str(exc), retryable=False)

    scope = check_scope(assignment)
    if scope.status == "needs_input":
        return EngineNeedsInput(
            assignment_id=assignment.assignment_id,
            questions=scope.questions,
            missing_fields=scope.missing_fields,
            model_calls=getattr(model_client, "call_count", 0),
        )

    repository = repository or FixtureEvidenceRepository()
    access_context = access_context or AccessContext()
    retrieval = retrieve_for_assignment(
        assignment,
        repository,
        access_context,
        max_chunks=max_chunks,
        max_context_words=max_context_words,
    )

    if not retrieval.evidence:
        return EngineEvidenceGap(
            assignment_id=assignment.assignment_id,
            message=(
                "No eligible evidence was retrieved. Add an allowed source, broaden the approved corpus, "
                "or clarify the request before generation."
            ),
            query=retrieval.trace.query,
            rejected_chunk_ids=retrieval.trace.rejected_chunk_ids,
            model_calls=getattr(model_client, "call_count", 0),
        )

    generation_context, evidence_map, cost_evidence = build_generation_context(
        assignment,
        retrieval.evidence,
        repository,
        retrieval.trace.query,
    )

    try:
        raw_report, usage = model_client.generate(
            assignment,
            retrieval.evidence,
            generation_context=generation_context,
        )
        report = validate_report(
            raw_report,
            {e.chunk_id for e in retrieval.evidence},
            assignment.required_sections,
        )
        # Cost arithmetic is deterministic code, not generated model arithmetic.
        report.cost_evidence = cost_evidence
    except (ValidationError, ValueError, KeyError) as exc:
        return EngineFailure(code="invalid_model_output", message=str(exc), retryable=False)

    return EngineSuccess(
        report=report,
        usage=usage,
        retrieval_trace=retrieval.trace,
        evidence_map=evidence_map,
        methodology_stages=METHODOLOGY_STAGES,
    )
