-- this file connects past work to evidence and saves reports without changing old versions
-- each fact points back to a chunk so we can check where it came from
CREATE TABLE engagement_facts (
    fact_id UUID PRIMARY KEY,
    engagement_id UUID NOT NULL REFERENCES engagements,
    kind TEXT NOT NULL CHECK (kind IN ('specialty','method','deliverable','recommendation','outcome','related_engagement','contract_value')),
    value TEXT,
    unknown_reason TEXT,
    evidence_chunk_id UUID NOT NULL REFERENCES chunks,
    related_engagement_id UUID REFERENCES engagements,
    amount NUMERIC(18,2),
    currency TEXT,
    CHECK ((value IS NOT NULL AND btrim(value) <> '' AND unknown_reason IS NULL)
        OR (kind='outcome' AND value IS NULL AND btrim(unknown_reason) <> '' AND unknown_reason IS NOT NULL)),
    CHECK ((kind='related_engagement') = (related_engagement_id IS NOT NULL)),
    CHECK (related_engagement_id IS NULL OR related_engagement_id <> engagement_id),
    CHECK ((kind='contract_value' AND amount IS NOT NULL AND amount >= 0 AND amount <> 'NaN'::numeric
        AND currency IS NOT NULL AND currency ~ '^[A-Z]{3}$')
        OR (kind<>'contract_value' AND amount IS NULL AND currency IS NULL))
);
CREATE INDEX engagement_facts_engagement ON engagement_facts(engagement_id);
CREATE TABLE engagement_documents (
    engagement_id UUID NOT NULL REFERENCES engagements,
    document_version_id UUID NOT NULL REFERENCES document_versions,
    PRIMARY KEY(engagement_id, document_version_id)
);
CREATE TABLE reports (
    report_id UUID PRIMARY KEY,
    assignment_id UUID NOT NULL REFERENCES assignments,
    actor_id UUID NOT NULL
);
CREATE TABLE report_versions (
    report_version_id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES reports,
    version INTEGER NOT NULL CHECK(version > 0),
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(report_id, version)
);
-- this pair makes it impossible to attach a chunk to the wrong source version
ALTER TABLE chunks ADD CONSTRAINT chunks_version_pair UNIQUE(chunk_id, document_version_id);
CREATE TABLE report_citations (
    report_version_id UUID NOT NULL REFERENCES report_versions,
    citation_id TEXT NOT NULL CHECK(btrim(citation_id) <> ''),
    chunk_id UUID NOT NULL,
    document_version_id UUID NOT NULL,
    PRIMARY KEY(report_version_id, citation_id),
    FOREIGN KEY(chunk_id, document_version_id) REFERENCES chunks(chunk_id, document_version_id)
);
CREATE TRIGGER report_versions_append_only BEFORE UPDATE OR DELETE ON report_versions
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
CREATE TRIGGER report_citations_append_only BEFORE UPDATE OR DELETE ON report_citations
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
