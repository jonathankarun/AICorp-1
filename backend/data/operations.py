# this file handles corrections, source access, and report reviews
# basically we keep the old decision so we can explain what changed later
from typing import Literal
from uuid import UUID
from pydantic import Field
from psycopg.types.json import Jsonb
from .models import Contract
from .workspace import DataError, require_department, list_documents
from .reports import get_report

Category = Literal['consulting', 'operational', 'unresolved']

class CorrectionInput(Contract):
    expected_classification: Category
    classification: Category
    reason: str = Field(min_length=1, max_length=2000)

class RestrictionInput(Contract):
    blocked: bool
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=2000)

class ReviewInput(Contract):
    decision: Literal['reviewed', 'changes_requested', 'approved']
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=2000)


def require_role(conn, context, *, administrator=False):
    row = conn.execute('SELECT role FROM data_roles WHERE actor_id=%s', (context.actor_id,)).fetchone()
    if not row or (administrator and row['role'] != 'administrator'):
        raise DataError('review_permission_required', 403)


def audit(conn, context, action, identifier, old, new, reason):
    if not reason.strip():
        raise DataError('reason_required', 422)
    conn.execute('INSERT INTO data_audit(actor_id,action,resource_id,old_value,new_value,reason) VALUES(%s,%s,%s,%s,%s,%s)',
                 (context.actor_id, action, identifier, Jsonb(old), Jsonb(new), reason.strip()))


def correct_payment(conn, identifier: UUID, data: CorrectionInput, context):
    with conn.transaction():
        require_role(conn, context)
        row = conn.execute('SELECT * FROM payments WHERE payment_id=%s FOR UPDATE', (identifier,)).fetchone()
        if not row:
            raise DataError('not_found', 404)
        require_department(context, row['department_id'])
        if row['classification'] != data.expected_classification:
            raise DataError('classification_conflict', 409)
        if row['classification'] == data.classification:
            raise DataError('classification_unchanged', 409)
        audit(conn, context, 'payment_classification', identifier,
              {'classification': row['classification'], 'reason': row['classification_reason']},
              {'classification': data.classification, 'reason': data.reason}, data.reason)
        conn.execute('UPDATE payments SET classification=%s, classification_reason=%s WHERE payment_id=%s',
                     (data.classification, data.reason.strip(), identifier))
    return {'payment_id': identifier, 'classification': data.classification}


def restrict_document(conn, identifier, data: RestrictionInput, context):
    with conn.transaction():
        require_role(conn, context, administrator=True)
        row = conn.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE', (identifier,)).fetchone()
        if not row:
            raise DataError('not_found', 404)
        require_department(context, row['department_id'])
        previous = conn.execute('SELECT * FROM document_restrictions WHERE document_id=%s', (identifier,)).fetchone()
        revision = previous['revision'] if previous else 0
        if revision != data.expected_revision:
            raise DataError('permission_revision_conflict', 409)
        result = {'blocked': data.blocked, 'revision': revision + 1}
        audit(conn, context, 'document_access', identifier,
              {'blocked': previous['blocked'] if previous else False, 'revision': revision}, result, data.reason)
        conn.execute('INSERT INTO document_restrictions VALUES(%s,%s,%s) ON CONFLICT(document_id) DO UPDATE SET blocked=excluded.blocked,revision=excluded.revision',
                     (identifier, data.blocked, revision + 1))
    return result


def read_document(conn, identifier, context):
    source = next((d for d in list_documents(conn, context) if d['document_version_id'] == identifier), None)
    if source is None:
        raise DataError('not_found', 404)
    row = conn.execute("SELECT raw_bytes FROM ingestion_jobs WHERE document_version_id=%s AND status='ready' LIMIT 1", (identifier,)).fetchone()
    return source, bytes(row['raw_bytes'])


def review_report(conn, identifier, version, data: ReviewInput, context):
    with conn.transaction():
        require_role(conn, context)
        report = get_report(conn, identifier, version, context)
        key = report['report_version_id']
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,1))', (str(key),))
        latest = conn.execute('SELECT * FROM report_reviews WHERE report_version_id=%s ORDER BY revision DESC LIMIT 1', (key,)).fetchone()
        revision = latest['revision'] if latest else 0
        if revision != data.expected_revision:
            raise DataError('review_revision_conflict', 409)
        # approving needs a recorded review first; a requested change needs a new draft
        if data.decision == 'approved' and (not latest or latest['decision'] != 'reviewed'):
            raise DataError('review_required', 409)
        if latest and latest['decision'] in ('approved', 'changes_requested'):
            raise DataError('new_report_version_required', 409)
        if not data.reason.strip():
            raise DataError('reason_required', 422)
        return conn.execute('INSERT INTO report_reviews VALUES(%s,%s,%s,%s,%s,DEFAULT) RETURNING *',
                            (key, revision + 1, context.actor_id, data.decision, data.reason.strip())).fetchone()
