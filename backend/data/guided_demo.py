"""Run real subsystem operations in a rollback-only transaction for presentations."""
import base64
import json
from uuid import uuid4

from .demo import FIX, DEPARTMENT
from .ingestion import submit_pdf, process_job
from .importer import import_csv, spending
from .operations import CorrectionInput, correct_payment, read_document, require_role
from .search import search
from .week2_models import AssignmentInput, DocumentInput, SearchInput
from .workspace import get_job, save_assignment, get_assignment, require_department, DataError


def run_guided_demo(conn, context):
    # All nested service transactions become savepoints. Even on failure, none of
    # this run's records commit. Unique import keys never touch existing payments.
    with conn.transaction(force_rollback=True):
        require_department(context, DEPARTMENT)
        require_role(conn, context)
        run_id = str(uuid4())
        manifest = json.loads((FIX / 'manifest.json').read_text())
        manifest['source_key'] = 'guided-' + run_id
        job_id = submit_pdf(conn, (FIX / 'engagement.pdf').read_bytes(),
                            DocumentInput(**manifest['pdf']), context)
        if process_job(conn, job_id) != 'ready':
            raise DataError('demo_extraction_failed', 422)
        job = get_job(conn, job_id, context)
        version = job['document_version_id']
        extracted = conn.execute('SELECT page_number,text FROM chunks WHERE document_version_id=%s ORDER BY ordinal', (version,)).fetchall()
        assignment = save_assignment(conn, AssignmentInput(
            problem='Improve permit intake', intended_result='A preliminary improvement plan',
            department_id=DEPARTMENT, selected_document_version_ids=[version]), context)
        restored = get_assignment(conn, assignment['assignment_id'], context)
        evidence = search(conn, SearchInput(query='timeline',
            selected_document_version_ids=[version], for_external_model=False), context)
        _, pdf = read_document(conn, version, context)
        imported = import_csv(conn, (FIX / 'payments.csv').read_bytes(), manifest)
        if imported['rejected']:
            raise DataError('demo_import_failed', 422)
        budget = json.loads((FIX / 'budget.json').read_text())
        budget['source_key'] = manifest['source_key']
        def totals():
            return spending(conn, department_id=DEPARTMENT, start=budget['start'],
                end=budget['end'], budget=budget, source_key=manifest['source_key'])
        before = totals()
        payment = conn.execute('SELECT payment_id FROM payments WHERE source_key=%s',
                               (manifest['source_key'] + ':p-005',)).fetchone()
        correct_payment(conn, payment['payment_id'], CorrectionInput(
            expected_classification='unresolved', classification='consulting',
            reason='Scripted fictional demo decision: classify the sample $50 as consulting; not a human review.'), context)
        after = totals()
        audit = conn.execute('SELECT * FROM data_audit WHERE resource_id=%s ORDER BY audit_id',
                             (payment['payment_id'],)).fetchall()
        result = dict(run_id=run_id, mode='rollback-only', job=job, extracted=extracted,
                      assignment=restored, evidence=evidence, imported=imported,
                      before=before, after=after, audit=audit,
                      pdf_base64=base64.b64encode(pdf).decode('ascii'))
    return result
