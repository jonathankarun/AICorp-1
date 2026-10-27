-- this keeps permissions and review decisions separate from the original evidence
CREATE TABLE data_roles (
    actor_id UUID PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('reviewer','administrator'))
);
CREATE TABLE document_restrictions (
    document_id UUID PRIMARY KEY REFERENCES documents,
    blocked BOOLEAN NOT NULL,
    revision INTEGER NOT NULL CHECK(revision > 0)
);
CREATE TABLE data_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    actor_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_id UUID NOT NULL,
    old_value JSONB,
    new_value JSONB NOT NULL,
    reason TEXT NOT NULL CHECK(btrim(reason) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER data_audit_append_only BEFORE UPDATE OR DELETE ON data_audit
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
CREATE TABLE report_reviews (
    report_version_id UUID NOT NULL REFERENCES report_versions,
    revision INTEGER NOT NULL CHECK(revision > 0),
    actor_id UUID NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('reviewed','changes_requested','approved')),
    reason TEXT NOT NULL CHECK(btrim(reason) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(report_version_id, revision)
);
CREATE TRIGGER report_reviews_append_only BEFORE UPDATE OR DELETE ON report_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
