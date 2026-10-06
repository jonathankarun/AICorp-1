from __future__ import annotations

from pydantic import ValidationError

from .adapters import ModelAdapter
from .models import (
    Assignment,
    EngineFailure,
    EngineNeedsInput,
    EngineResult,
    EngineSuccess,
    Report,
)
from .repository import get_fixture_evidence
from .scope import check_scope


def validate_assignment(data: dict | Assignment) -> Assignment:
    return data if isinstance(data, Assignment) else Assignment.model_validate(data)


def retrieve_evidence(assignment: Assignment):
    return get_fixture_evidence(assignment)


def validate_report(raw_report: dict, valid_evidence_ids: set[str]) -> Report:
    report = Report.model_validate(raw_report)
    for citation in report.citations:
        if citation.evidence_chunk_id not in valid_evidence_ids:
            raise ValueError(
                f"citation '{citation.citation_id}' points to unknown evidence chunk "
                f"'{citation.evidence_chunk_id}'"
            )
    return report


def run_engine(
    data: dict | Assignment, model_client: ModelAdapter, evidence_repository=None
) -> EngineResult:
    try:
        assignment = validate_assignment(data)
    except ValidationError as exc:
        return EngineFailure(
            code="invalid_assignment", message=str(exc), retryable=False
        )

    scope = check_scope(assignment)
    if scope.status == "needs_input":
        return EngineNeedsInput(
            assignment_id=assignment.assignment_id,
            questions=scope.questions,
            missing_fields=scope.missing_fields,
            model_calls=getattr(model_client, "call_count", 0),
        )

    try:
        evidence = (evidence_repository or retrieve_evidence)(assignment)
    except ValueError:
        return EngineFailure(
            code="invalid_retrieval_request",
            message="Check source IDs and the evidence contract.",
            retryable=False,
        )
    if not evidence:
        return EngineNeedsInput(
            assignment_id=assignment.assignment_id,
            questions=["Provide readable, approved sources for this assignment."],
            missing_fields=["eligible_evidence"],
            model_calls=getattr(model_client, "call_count", 0),
        )

    try:
        raw_report, usage = model_client.generate(assignment, evidence)
        report = validate_report(raw_report, {e.chunk_id for e in evidence})
    except (ValidationError, ValueError, KeyError) as exc:
        return EngineFailure(
            code="invalid_model_output", message=str(exc), retryable=False
        )

    return EngineSuccess(report=report, usage=usage)
