-- Mutable workflow state is separate from append-only evidence.
CREATE TABLE assignments (
    assignment_id UUID PRIMARY KEY,
    actor_id UUID NOT NULL,
    department_id UUID NOT NULL REFERENCES departments,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    department_id UUID NOT NULL REFERENCES departments,
    actor_id UUID NOT NULL
);
CREATE TABLE ingestion_jobs (
    job_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents,
    status TEXT NOT NULL CHECK(status IN ('pending','processing','ready','failed')),
    metadata JSONB NOT NULL,
    raw_bytes BYTEA NOT NULL,
    content_hash TEXT NOT NULL,
    document_version_id UUID REFERENCES document_versions,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((status = 'ready') = (document_version_id IS NOT NULL))
);
CREATE TABLE assignment_sources (
    assignment_id UUID NOT NULL REFERENCES assignments,
    document_version_id UUID NOT NULL REFERENCES document_versions,
    PRIMARY KEY(assignment_id, document_version_id)
);
CREATE TABLE source_imports (
    import_id UUID PRIMARY KEY,
    source_key TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    manifest JSONB NOT NULL,
    raw_bytes BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE import_rows (
    import_id UUID NOT NULL REFERENCES source_imports,
    row_number INTEGER NOT NULL,
    raw_record JSONB NOT NULL,
    outcome TEXT NOT NULL,
    reason TEXT,
    payment_id UUID REFERENCES payments,
    PRIMARY KEY(import_id,row_number)
);
CREATE TABLE payment_revisions (
    revision_id BIGSERIAL PRIMARY KEY,
    payment_id UUID NOT NULL REFERENCES payments,
    import_id UUID NOT NULL REFERENCES source_imports,
    old_record JSONB,
    new_record JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Direct department scope is needed for payments with no known engagement.
ALTER TABLE payments ADD COLUMN department_id UUID REFERENCES departments;
UPDATE payments p SET department_id=e.department_id FROM engagements e
WHERE p.engagement_id=e.engagement_id;
CREATE TABLE search_runs (
    search_id UUID PRIMARY KEY,
    actor_id UUID NOT NULL,
    query TEXT NOT NULL,
    filters JSONB NOT NULL,
    returned_ids JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
