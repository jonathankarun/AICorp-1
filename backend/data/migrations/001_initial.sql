-- Week 1: source-linked entities, exact money, and versioned evidence structure.
CREATE TABLE departments (
    department_id UUID PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE CHECK (btrim(source_key) <> ''),
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    source_uri TEXT NOT NULL CHECK (btrim(source_uri) <> '')
);

CREATE TABLE vendors (
    vendor_id UUID PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE CHECK (btrim(source_key) <> ''),
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    source_uri TEXT NOT NULL CHECK (btrim(source_uri) <> '')
);

CREATE TABLE engagements (
    engagement_id UUID PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE CHECK (btrim(source_key) <> ''),
    department_id UUID NOT NULL REFERENCES departments(department_id),
    vendor_id UUID NOT NULL REFERENCES vendors(vendor_id),
    title TEXT NOT NULL CHECK (btrim(title) <> ''),
    source_uri TEXT NOT NULL CHECK (btrim(source_uri) <> ''),
    -- Allows the payment FK to enforce vendor agreement with its engagement.
    UNIQUE (engagement_id, vendor_id)
);

CREATE TABLE payments (
    payment_id UUID PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE CHECK (btrim(source_key) <> ''),
    vendor_id UUID NOT NULL REFERENCES vendors(vendor_id),
    engagement_id UUID,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount <> 'NaN'::numeric),
    currency TEXT NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    paid_on DATE NOT NULL,
    classification TEXT NOT NULL DEFAULT 'unresolved'
        CHECK (classification IN ('consulting', 'operational', 'unresolved')),
    classification_reason TEXT NOT NULL CHECK (btrim(classification_reason) <> ''),
    source_uri TEXT NOT NULL CHECK (btrim(source_uri) <> ''),
    FOREIGN KEY (engagement_id, vendor_id)
        REFERENCES engagements(engagement_id, vendor_id)
);

CREATE TABLE document_versions (
    document_version_id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    engagement_id UUID REFERENCES engagements(engagement_id),
    title TEXT NOT NULL CHECK (btrim(title) <> ''),
    issuer TEXT,
    published_on DATE,
    source_uri TEXT NOT NULL CHECK (btrim(source_uri) <> ''),
    content_hash TEXT NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    extraction_version TEXT,
    access_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (access_status IN ('unknown', 'public', 'restricted')),
    external_model_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (document_id, version),
    CHECK (NOT external_model_allowed OR access_status <> 'unknown')
);

CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    document_version_id UUID NOT NULL REFERENCES document_versions(document_version_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    text TEXT NOT NULL CHECK (btrim(text) <> ''),
    content_hash TEXT NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    UNIQUE (document_version_id, ordinal)
);

-- Document versions and their extracted chunks are append-only in this prototype.
-- Re-extraction should produce a new version, preserving earlier citations.
CREATE FUNCTION reject_evidence_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Evidence versions are append-only; insert a new version'
        USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER document_versions_append_only BEFORE UPDATE OR DELETE ON document_versions
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
CREATE TRIGGER chunks_append_only BEFORE UPDATE OR DELETE ON chunks
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();

