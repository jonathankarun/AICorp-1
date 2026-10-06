from __future__ import annotations

from dataclasses import dataclass

from .demo_models import AccessContext, Assignment, EvidenceChunk, RetrievalTrace
from .demo_repository import EvidenceRepository


@dataclass
class RetrievalBundle:
    evidence: list[EvidenceChunk]
    trace: RetrievalTrace


def prepare_query(assignment: Assignment) -> str:
    parts = [assignment.problem]
    if assignment.intended_result:
        parts.append(assignment.intended_result)
    if assignment.topic:
        parts.append(assignment.topic)
    if assignment.required_sections:
        parts.append(" ".join(assignment.required_sections))
    return " ".join(part.strip() for part in parts if part and part.strip())


def _select_context(
    query: str,
    candidates: list[EvidenceChunk],
    access_context: AccessContext,
    *,
    selected_document_version_ids: list[str] | None = None,
    max_chunks: int = 5,
    max_context_words: int = 450,
) -> RetrievalBundle:
    selected: list[EvidenceChunk] = []
    rejected: list[str] = []
    seen: set[str] = set()
    word_count = 0

    for chunk in candidates:
        if chunk.access_scope not in access_context.readable_scopes:
            rejected.append(chunk.chunk_id)
            continue
        if access_context.external_model_use and not chunk.external_model_allowed:
            rejected.append(chunk.chunk_id)
            continue

        dedupe_key = chunk.content_hash or " ".join(chunk.text.lower().split())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        chunk_words = len(chunk.text.split())
        if word_count + chunk_words > max_context_words:
            continue
        if len(selected) >= max_chunks:
            break
        selected.append(chunk)
        word_count += chunk_words

    trace = RetrievalTrace(
        query=query,
        filters={
            "access_scopes": access_context.readable_scopes,
            "external_model_use": access_context.external_model_use,
            "selected_documents_constrain_search": bool(selected_document_version_ids),
        },
        candidate_chunk_ids=[chunk.chunk_id for chunk in candidates],
        selected_chunk_ids=[chunk.chunk_id for chunk in selected],
        rejected_chunk_ids=rejected,
        selected_document_version_ids=selected_document_version_ids or [],
        context_word_count=word_count,
        max_chunks=max_chunks,
        max_context_words=max_context_words,
    )
    return RetrievalBundle(evidence=selected, trace=trace)


def retrieve_for_assignment(
    assignment: Assignment,
    repository: EvidenceRepository,
    access_context: AccessContext,
    *,
    max_chunks: int = 5,
    max_context_words: int = 450,
) -> RetrievalBundle:
    query = prepare_query(assignment)
    candidates = repository.search_evidence(
        query,
        selected_document_version_ids=assignment.selected_document_version_ids,
        department_id=assignment.department_id,
    )
    return _select_context(
        query,
        candidates,
        access_context,
        selected_document_version_ids=assignment.selected_document_version_ids,
        max_chunks=max_chunks,
        max_context_words=max_context_words,
    )


def retrieve_query(
    query: str,
    repository: EvidenceRepository,
    access_context: AccessContext,
    *,
    selected_document_version_ids: list[str] | None = None,
    department_id: str | None = "dept-fixture-001",
    max_chunks: int = 5,
    max_context_words: int = 450,
) -> RetrievalBundle:
    candidates = repository.search_evidence(
        query,
        selected_document_version_ids=selected_document_version_ids,
        department_id=department_id,
    )
    return _select_context(
        query,
        candidates,
        access_context,
        selected_document_version_ids=selected_document_version_ids,
        max_chunks=max_chunks,
        max_context_words=max_context_words,
    )
