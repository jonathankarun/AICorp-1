"""The guided run uses real services, repeats cleanly, and never changes saved work."""
from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.data.db import connect
from backend.data.demo import prepare_demo, demo_spending
from backend.data.operations import correct_payment, CorrectionInput
from test_week2 import database, CTX, TOKEN


def snapshot(conn):
    tables = ['documents', 'document_versions', 'chunks', 'ingestion_jobs',
              'assignments', 'assignment_sources', 'payments', 'source_imports',
              'import_rows', 'payment_revisions', 'data_audit']
    return {t: conn.execute(f'SELECT count(*) AS n FROM {t}').fetchone()['n'] for t in tables}


def test_guided_run_is_real_repeatable_and_isolated(database):
    prepare_demo(database, CTX)
    existing = demo_spending(database, CTX)
    payment = next(p for p in existing['payments'] if p['classification'] == 'unresolved')
    correct_payment(database, payment['payment_id'], CorrectionInput(
        expected_classification='unresolved', classification='consulting', reason='Existing user review'), CTX)
    database.commit()
    before = snapshot(database)
    app = create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True)
    with TestClient(app) as client:
        assert client.post('/api/v1/demo/run').status_code == 401
        runs = []
        for _ in range(2):
            response = client.post('/api/v1/demo/run', headers={'Authorization': 'Bearer ' + TOKEN})
            assert response.status_code == 200, response.text
            run = response.json()
            assert run['job']['status'] == 'ready'
            assert 'six weeks' in run['evidence']['chunks'][0]['text']
            assert run['assignment']['selected_document_version_ids'] == [run['job']['document_version_id']]
            assert run['imported']['inserted'] == 5
            assert run['before']['consulting'] == '280.00'
            assert run['after']['consulting'] == '330.00'
            assert run['audit'][0]['old_value']['classification'] == 'unresolved'
            assert run['pdf_base64'].startswith('JVBER')
            assert snapshot(database) == before
            assert demo_spending(database, CTX)['totals']['consulting'] == '330.00'
            runs.append(run['run_id'])
        assert runs[0] != runs[1]
        database.execute('DELETE FROM data_roles WHERE actor_id=%s', (CTX.actor_id,))
        database.commit()
        assert client.post('/api/v1/demo/run', headers={'Authorization': 'Bearer ' + TOKEN}).status_code == 403
        assert snapshot(database) == before


def test_failed_guided_run_rolls_back_partial_writes(database, monkeypatch):
    from backend.data import guided_demo
    from backend.data.workspace import DataError
    prepare_demo(database, CTX)
    before = snapshot(database)
    real_correction = guided_demo.correct_payment

    def fail_after_correction(*args, **kwargs):
        real_correction(*args, **kwargs)
        raise DataError('injected_demo_failure', 422)

    monkeypatch.setattr(guided_demo, 'correct_payment', fail_after_correction)
    app = create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True)
    with TestClient(app) as client:
        response = client.post('/api/v1/demo/run', headers={'Authorization': 'Bearer ' + TOKEN})
        assert response.status_code == 422
        assert response.json()['error']['code'] == 'injected_demo_failure'
    assert snapshot(database) == before
    assert demo_spending(database, CTX)['totals']['consulting'] == '280.00'
