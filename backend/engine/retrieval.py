"""Real evidence adapter: explicit filters, deduplication, bounded text context."""

from uuid import UUID
from backend.data.models import AccessContext
from backend.data.search import search
from backend.data.week2_models import SearchInput
from .models import EvidenceChunk


class DataEvidenceRepository:
    def __init__(self, connection, context, max_chars=6000):
        if max_chars < 1:
            raise ValueError("max_chars must be positive")
        self.connection, self.context, self.max_chars = connection, context, max_chars
        self.last_result = None

    def __call__(self, assignment):
        # Empty UI selection means search all eligible sources. An explicit []
        # at the lower-level search API means search no versions.
        query = " ".join(filter(None, [assignment.problem, assignment.intended_result]))
        request = SearchInput(
            query=query[:2000],
            selected_document_version_ids=assignment.selected_document_version_ids
            or None,
            limit=20,
            for_external_model=True,
        )
        department = (
            UUID(assignment.department_id) if assignment.department_id else None
        )
        scoped_context = AccessContext(
            actor_id=self.context.actor_id,
            allowed_department_ids=(department,)
            if department in self.context.allowed_department_ids
            else (),
        )
        self.last_result = search(self.connection, request, scoped_context)
        seen, result, remaining = set(), [], self.max_chars
        for row in self.last_result["chunks"]:
            if row["content_hash"] in seen or len(row["text"]) > remaining:
                continue
            # Search enforces membership and ready status in SQL; this checks
            # the separate outbound-model permission at the engine boundary.
            if not row["external_model_allowed"] or row["access_status"] == "unknown":
                raise ValueError("Ineligible evidence returned by repository")
            seen.add(row["content_hash"])
            remaining -= len(row["text"])
            result.append(
                EvidenceChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_version_id=str(row["document_version_id"]),
                    title=row["title"],
                    source_uri=row["source_uri"],
                    locator=row["locator"],
                    text=row["text"],
                    access_scope=row["access_status"],
                    external_model_allowed=row["external_model_allowed"],
                )
            )
        return result
