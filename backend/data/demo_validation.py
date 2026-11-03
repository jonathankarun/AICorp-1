"""Presentation checks against real services, with all fixture writes rolled back."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import time
from uuid import uuid4

from .demo import FIX, DEPARTMENT
from .guided_demo import run_guided_demo
from .importer import import_csv
from .ingestion import submit_pdf, process_job
from .models import AccessContext
from .operations import correct_payment, CorrectionInput, require_role
from .week2_models import DocumentInput
from .workspace import DataError, get_job, require_department

TABLES = ('documents', 'document_versions', 'chunks', 'ingestion_jobs', 'assignments',
          'assignment_sources', 'payments', 'source_imports', 'import_rows',
          'payment_revisions', 'data_audit', 'search_runs')


def record_fingerprints(conn):
    # Fixed table names only. Hash complete rows, not just counts; never return
    # other users' record contents in the validation response.
    return {table: conn.execute(f'''SELECT count(*) AS count,
        md5(coalesce(string_agg(h, '' ORDER BY h), '')) AS fingerprint
        FROM (SELECT md5(to_jsonb(t)::text) AS h FROM {table} t) rows''').fetchone()
        for table in TABLES}


def validate_demo(conn, context):
    require_department(context, DEPARTMENT)
    require_role(conn, context)
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    checks = []

    def check(name, expected, actual):
        checks.append(dict(name=name, expected=expected, actual=actual,
                           status='PASS' if expected == actual else 'FAIL'))

    def error(name, exc):
        # Avoid exposing database details or arbitrary exception messages.
        checks.append(dict(name=name, expected='Operation completes',
            actual=exc.code if isinstance(exc, DataError) else type(exc).__name__, status='ERROR'))

    with conn.transaction(force_rollback=True):
        baseline = record_fingerprints(conn)
        runs = []
        for attempt in range(2):
            try:
                # A savepoint contains even an unexpected service failure.
                with conn.transaction(force_rollback=True):
                    run = run_guided_demo(conn, context)
                    unchanged = record_fingerprints(conn) == baseline
                runs.append(run)
                check(f'Run {attempt + 1}: temporary records removed', True, unchanged)
            except Exception as exc:
                error(f'Run {attempt + 1}: workflow execution', exc)
        if runs:
            run = runs[0]
            check('PDF processing', {'status': 'ready', 'contains_six_weeks': True},
                  {'status': run['job']['status'], 'contains_six_weeks': any('six weeks' in c['text'] for c in run['extracted'])})
            check('Assignment write and read-back',
                  {'problem': 'Improve permit intake', 'intended_result': 'A preliminary improvement plan',
                   'source_versions': [str(run['job']['document_version_id'])]},
                  {'problem': run['assignment']['problem'], 'intended_result': run['assignment']['intended_result'],
                   'source_versions': [str(v) for v in run['assignment']['selected_document_version_ids']]})
            chunks = run['evidence']['chunks']
            check('Evidence retrieval', {'matching_passage_on_page_1': True, 'only_selected_version': True},
                  {'matching_passage_on_page_1': any('six weeks' in c['text'] and c['locator'] == 'page 1' for c in chunks),
                   'only_selected_version': bool(chunks) and all(c['document_version_id'] == run['job']['document_version_id'] for c in chunks)})
            check('Original PDF integrity (SHA-256)', hashlib.sha256((FIX / 'engagement.pdf').read_bytes()).hexdigest(),
                  hashlib.sha256(base64.b64decode(run['pdf_base64'])).hexdigest())
            check('Payment import', {'inserted': 5, 'rejected': 0},
                  {'inserted': run['imported']['inserted'], 'rejected': len(run['imported']['rejected'])})
            keys = ('consulting', 'operational', 'unresolved', 'consulting_share_percent')
            check('Initial spending', dict(zip(keys, ('280.00', '500.00', '50.00', '2.80'))),
                  {k: run['before'][k] for k in keys})
            check('Corrected spending', dict(zip(keys, ('330.00', '500.00', '0.00', '3.30'))),
                  {k: run['after'][k] for k in keys})
            audit = run['audit']
            check('Correction audit history',
                  {'entries': 1, 'old': 'unresolved', 'new': 'consulting', 'actor_matches': True, 'reason_and_time': True},
                  {'entries': len(audit), 'old': audit[0]['old_value']['classification'] if audit else None,
                   'new': audit[0]['new_value']['classification'] if audit else None,
                   'actor_matches': bool(audit) and audit[0]['actor_id'] == context.actor_id,
                   'reason_and_time': bool(audit) and bool(audit[0]['reason'].strip() and audit[0]['created_at'])})
        else:
            checks.append(dict(name='Workflow result checks', expected='Completed workflow results',
                               actual='No results available', status='SKIP'))
        if len(runs) == 2:
            check('Repeatable results', {'same_totals': True, 'distinct_run_ids': True},
                  {'same_totals': all(runs[0][phase][key] == runs[1][phase][key]
                                      for phase in ('before', 'after') for key in (*keys, 'budget')),
                   'distinct_run_ids': runs[0]['run_id'] != runs[1]['run_id']})
        else:
            checks.append(dict(name='Repeatable results', expected='Two completed runs', actual=f'{len(runs)} completed runs', status='SKIP'))

        try:
            with conn.transaction(force_rollback=True):
                meta = DocumentInput(**json.loads((FIX / 'manifest.json').read_text())['pdf'])
                job_id = submit_pdf(conn, b'%PDF-1.4\nbroken', meta, context)
                process_job(conn, job_id)
                job = get_job(conn, job_id, context)
                check('Unreadable PDF rejected', {'status': 'failed', 'error': 'unreadable_pdf'},
                      {'status': job['status'], 'error': job['error_code']})
        except Exception as exc:
            error('Unreadable PDF rejected', exc)

        try:
            with conn.transaction(force_rollback=True):
                manifest = json.loads((FIX / 'manifest.json').read_text())
                manifest['source_key'] = 'validation-' + uuid4().hex
                import_csv(conn, (FIX / 'payments.csv').read_bytes(), manifest)
                payment = conn.execute('SELECT payment_id FROM payments WHERE source_key=%s',
                                       (manifest['source_key'] + ':p-005',)).fetchone()
                before_denial = record_fingerprints(conn)
                reader = AccessContext(actor_id=uuid4(), allowed_department_ids=(DEPARTMENT,))
                outcome = 'Correction was allowed'
                try:
                    correct_payment(conn, payment['payment_id'], CorrectionInput(
                        expected_classification='unresolved', classification='consulting', reason='Validation permission probe'), reader)
                except DataError as exc:
                    outcome = f'{exc.status} {exc.code}'
                check('Unauthorized correction denied', '403 review_permission_required', outcome)
                check('Denied correction leaves records unchanged', True, record_fingerprints(conn) == before_denial)
        except Exception as exc:
            error('Unauthorized correction denied', exc)
        check('Saved records unchanged across checked tables', True, record_fingerprints(conn) == baseline)

    passed = sum(c['status'] == 'PASS' for c in checks)
    return dict(schema_version='1.0', run_id=str(uuid4()), started_at=started.isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(), duration_ms=round((time.perf_counter() - clock) * 1000),
                status='PASS' if passed == len(checks) else 'FAIL', passed=passed, total=len(checks), checks=checks,
                scope='Local fictional fixtures; real service calls in rollback-only transactions. Tests transaction read-back, not persistence after restart. Record contents in the checked tables must stay unchanged; sequence counters may advance.',
                checked_tables=list(TABLES))
