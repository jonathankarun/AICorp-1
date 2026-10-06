"""Bridge the persisted workspace to Jai's Week 2/3 engine contracts.

The local adapter quotes retrieved evidence; it does not claim to generate a
consulting recommendation or reuse synthetic fixture citations for real UUIDs.
"""

from uuid import UUID, uuid4

from backend.data.models import AccessContext
from backend.data.search import search
from backend.data.week2_models import SearchInput
from .demo_models import EvidenceChunk, UsageRecord


class WorkspaceEvidenceRepository:
    def __init__(self, connection, context):
        self.connection = connection
        self.context = context

    def search_evidence(self, query, *, selected_document_version_ids=None,
                        department_id=None):
        department = UUID(department_id) if department_id else None
        scoped = AccessContext(
            actor_id=self.context.actor_id,
            allowed_department_ids=(department,)
            if department in self.context.allowed_department_ids else (),
        )
        result = search(self.connection, SearchInput(
            query=query[:2000],
            selected_document_version_ids=selected_document_version_ids or None,
            limit=20, for_external_model=True,
        ), scoped)
        return [EvidenceChunk(
            chunk_id=str(row["chunk_id"]),
            document_version_id=str(row["document_version_id"]),
            title=row["title"], source_uri=row["source_uri"],
            locator=row["locator"], text=row["text"],
            content_hash=row["content_hash"], department_id=str(department),
            access_scope=row["access_status"],
            external_model_allowed=row["external_model_allowed"],
        ) for row in result["chunks"]]

    def get_historical_costs(self, query, department_id):
        # Assignment inputs have no comparison population, date or budget scope.
        # Do not substitute Jai's synthetic costs or Jonathan's aggregate totals.
        return []


class WorkspaceMockAdapter:
    """Deterministic, explicitly mock evidence preview with resolvable citations."""

    def __init__(self):
        self.call_count = 0
        self.evidence = []

    def generate(self, assignment, evidence, *, generation_context):
        self.call_count += 1
        self.evidence = evidence
        by_id = {chunk.chunk_id: chunk for chunk in evidence}
        citations = {chunk.chunk_id: f"cite-{i + 1}" for i, chunk in enumerate(evidence)}
        sections = []
        for entry in generation_context["evidence_map"]:
            ids = entry["supporting_chunk_ids"]
            excerpts = "\n\n".join(by_id[key].text for key in ids)
            sections.append({
                "name": entry["section"],
                "content": ("Mock evidence preview — source excerpts, not a generated recommendation.\n\n"
                            + excerpts) if ids else "No supporting evidence was retrieved for this section.",
                "citation_ids": [citations[key] for key in ids],
            })
        report = {
            "report_id": str(uuid4()), "assignment_id": assignment.assignment_id,
            "status": "draft", "sections": sections,
            "citations": [{"citation_id": value, "evidence_chunk_id": key}
                          for key, value in citations.items()],
            "assumptions": ["Local mock preview; no live model was called."],
            "missing_information": ["Comparable historical cost scope is not configured."],
            "expert_review_needed": ["A reviewer must develop and validate recommendations from these sources."],
        }
        return report, UsageRecord(
            provider="mock", model="workspace-evidence-preview-v1", prompt_version="v2",
            input_units=sum(len(chunk.text.split()) for chunk in evidence),
            output_units=sum(len(section["content"].split()) for section in sections),
        )
