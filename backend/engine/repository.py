from .models import Assignment, EvidenceChunk


FIXTURE_EVIDENCE = [
    EvidenceChunk(
        chunk_id="chunk-fixture-001",
        document_version_id="doc-fixture-v1",
        title="Fictional Process Improvement Project",
        source_uri="fixture://process-improvement/page-1",
        locator="page 1",
        text="The fictional department requests a preliminary improvement plan with a six-week implementation timeline.",
    ),
    EvidenceChunk(
        chunk_id="chunk-fixture-002",
        document_version_id="doc-fixture-v1",
        title="Fictional Process Improvement Project",
        source_uri="fixture://process-improvement/page-2",
        locator="page 2",
        text="Requested deliverables include findings, alternatives, an implementation plan, risks, and measures of success.",
    ),
]


def get_fixture_evidence(assignment: Assignment) -> list[EvidenceChunk]:
    # Week 1 deliberately uses a fixed synthetic fixture instead of live City data.
    return FIXTURE_EVIDENCE.copy()
