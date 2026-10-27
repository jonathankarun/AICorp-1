# this loads the fictional records once so the browser has something useful to show
# it never resets a database or changes a correction someone already made
import json
from uuid import UUID
from .db import ROOT
from .seed import seed
from .importer import import_csv, spending
from .ingestion import submit_pdf, process_job
from .week2_models import DocumentInput
from .history import add_fact
from .week3_models import FactInput

FIX = ROOT / 'tests/fixtures/week2'
DEPARTMENT = UUID('10000000-0000-4000-8000-000000000001')
ENGAGEMENT = UUID('30000000-0000-4000-8000-000000000001')
DOCUMENT = UUID('60000000-0000-4000-8000-000000000010')


def prepare_demo(conn, context):
    seed(conn)
    manifest = json.loads((FIX / 'manifest.json').read_text())
    # dont reimport over reviewed payment classifications when the server restarts
    if not conn.execute('SELECT 1 FROM source_imports WHERE source_key=%s', (manifest['source_key'],)).fetchone():
        import_csv(conn, (FIX / 'payments.csv').read_bytes(), manifest)
    conn.execute("INSERT INTO data_roles VALUES(%s,'administrator') ON CONFLICT DO NOTHING", (context.actor_id,))
    if not conn.execute('SELECT 1 FROM documents WHERE document_id=%s', (DOCUMENT,)).fetchone():
        conn.execute('INSERT INTO documents VALUES(%s,%s,%s)', (DOCUMENT, DEPARTMENT, context.actor_id))
    job = conn.execute("SELECT job_id FROM ingestion_jobs WHERE document_id=%s AND status='ready' LIMIT 1", (DOCUMENT,)).fetchone()
    if not job:
        identifier = submit_pdf(conn, (FIX / 'engagement.pdf').read_bytes(), DocumentInput(**manifest['pdf'], document_id=DOCUMENT), context)
        conn.commit()
        process_job(conn, identifier)
        conn.commit()
    chunk = conn.execute('SELECT c.* FROM chunks c JOIN document_versions v USING(document_version_id) WHERE v.document_id=%s ORDER BY v.version,c.ordinal LIMIT 1', (DOCUMENT,)).fetchone()
    if chunk and not conn.execute('SELECT 1 FROM engagement_facts WHERE engagement_id=%s', (ENGAGEMENT,)).fetchone():
        add_fact(conn, FactInput(engagement_id=ENGAGEMENT, kind='specialty', value='process improvement', evidence_chunk_id=chunk['chunk_id']), context)
        add_fact(conn, FactInput(engagement_id=ENGAGEMENT, kind='outcome', unknown_reason='The fixture does not provide a measured outcome', evidence_chunk_id=chunk['chunk_id']), context)
    conn.commit()


def demo_spending(conn, context):
    from .workspace import require_department
    require_department(context, DEPARTMENT)
    budget = json.loads((FIX / 'budget.json').read_text())
    totals = spending(conn, department_id=DEPARTMENT, start=budget['start'], end=budget['end'], budget=budget, source_key=budget['source_key'])
    rows = conn.execute('''SELECT p.* FROM payments p WHERE department_id=%s
        AND EXISTS (SELECT 1 FROM payment_revisions r JOIN source_imports s USING(import_id)
        WHERE r.payment_id=p.payment_id AND s.source_key=%s) ORDER BY paid_on,source_key''', (DEPARTMENT, budget['source_key'])).fetchall()
    events = conn.execute("SELECT a.* FROM data_audit a JOIN payments p ON p.payment_id=a.resource_id WHERE p.department_id=%s AND a.action='payment_classification' ORDER BY audit_id DESC", (DEPARTMENT,)).fetchall()
    return {'totals': totals, 'payments': rows, 'audit': events}
