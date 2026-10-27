# this checks the finished data workflows, including the cases we should reject
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.data.db import connect
from backend.data.demo import prepare_demo, demo_spending, DOCUMENT
from backend.data.operations import (correct_payment, restrict_document, review_report,
    read_document, CorrectionInput, RestrictionInput, ReviewInput)
from backend.data.workspace import DataError
from backend.data.reports import save_report, get_report
from backend.data.history import resolve_chunk, comparable_work
from backend.data.week3_models import ComparableInput
from backend.data.search import search
from backend.data.week2_models import SearchInput
from backend.data.recovery import backup, verify_restore
from test_week2 import database, CTX, TOKEN, DEPT
from test_week3 import source, draft


def grant(conn):
    conn.execute("INSERT INTO data_roles VALUES(%s,'administrator') ON CONFLICT DO NOTHING", (CTX.actor_id,))


def test_correction_audit_and_conflict(database):
    prepare_demo(database, CTX)
    initial = demo_spending(database, CTX)
    assert initial['totals']['consulting'] == '280.00'
    payment = next(p for p in initial['payments'] if p['classification'] == 'unresolved')
    change = CorrectionInput(expected_classification='unresolved', classification='consulting', reason='Checked the fixture evidence')
    correct_payment(database, payment['payment_id'], change, CTX)
    result = demo_spending(database, CTX)
    assert result['totals']['consulting'] == '330.00'
    assert result['totals']['unresolved'] == '0.00'
    assert result['audit'][0]['old_value']['classification'] == 'unresolved'
    with pytest.raises(DataError, match='classification_conflict'):
        correct_payment(database, payment['payment_id'], change, CTX)
    from backend.data.importer import import_csv
    from test_week2 import CSV, MANIFEST
    repeated = import_csv(database, CSV, MANIFEST)
    assert repeated['unchanged'] == 5
    prepare_demo(database, CTX)
    assert demo_spending(database, CTX)['totals']['consulting'] == '330.00' 


def test_revoke_blocks_all_source_paths_and_derived_reports(database):
    job, chunk = source(database)
    report = draft(database, chunk)
    save_report(database, report, CTX)
    grant(database)
    restrict_document(database, job['document_id'], RestrictionInput(blocked=True, expected_revision=0, reason='Source permission withdrawn'), CTX)
    for operation in [lambda: resolve_chunk(database, chunk['chunk_id'], CTX),
                      lambda: read_document(database, job['document_version_id'], CTX),
                      lambda: get_report(database, report.report_id, 1, CTX)]:
        with pytest.raises(DataError): operation()
    assert search(database, SearchInput(query='timeline', for_external_model=False), CTX)['chunks'] == []
    assert all(not c['documents'] for c in comparable_work(database, ComparableInput(for_external_model=False), CTX))
    restrict_document(database, job['document_id'], RestrictionInput(blocked=False, expected_revision=1, reason='Permission restored'), CTX)
    assert get_report(database, report.report_id, 1, CTX)['citations']


def test_reviews_require_role_and_version_check(database):
    _, chunk = source(database)
    report = draft(database, chunk)
    save_report(database, report, CTX)
    review = ReviewInput(decision='reviewed', expected_revision=0, reason='Checked the source')
    with pytest.raises(DataError, match='review_permission'):
        review_report(database, report.report_id, 1, review, CTX)
    grant(database)
    review_report(database, report.report_id, 1, review, CTX)
    with pytest.raises(DataError, match='review_revision_conflict'):
        review_report(database, report.report_id, 1, review, CTX)
    review_report(database, report.report_id, 1, ReviewInput(decision='approved', expected_revision=1, reason='Fixture approved'), CTX)
    assert len(get_report(database, report.report_id, 1, CTX)['reviews']) == 2
    report.version = 2
    save_report(database, report, CTX)
    assert get_report(database, report.report_id, 2, CTX)['reviews'] == []


def test_data_api_and_malformed_report(database):
    prepare_demo(database, CTX)
    database.commit()
    app = create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True)
    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer ' + TOKEN}
        assert client.get('/api/v1/demo/spending').status_code == 401
        assert client.get('/api/v1/demo/spending', headers=headers).json()['totals']['consulting'] == '280.00'
        cases = client.post('/api/v1/comparables', headers=headers, json={'topic': 'process', 'for_external_model': False}).json()
        assert cases[0]['facts']
        chunks = client.post('/api/v1/search', headers=headers, json={'query': 'timeline', 'for_external_model': False}).json()['chunks']
        identifier = chunks[0]['document_version_id']
        assert client.get(f'/api/v1/documents/{identifier}/pdf', headers=headers).content.startswith(b'%PDF')
        payload = {'report_id': 'bad-id', 'assignment_id': str(uuid4()), 'sections': [{'name': 'findings','content': 'test'}], 'citations': []}
        result = client.post('/api/v1/reports', headers=headers, json=payload)
        assert result.status_code == 422
        assert result.json()['error']['code'] == 'invalid_report_identifier'


def test_backup_restores_exact_rows_and_bytes(database, tmp_path):
    prepare_demo(database, CTX)
    _, chunk = source(database)
    report = draft(database, chunk)
    save_report(database, report, CTX)
    database.commit()
    destination = tmp_path / 'backup'
    backup(destination, database.info.dbname)
    assert verify_restore(destination)['passed']
    (destination / 'database.dump').write_bytes(b'broken')
    with pytest.raises(ValueError, match='checksum'):
        verify_restore(destination)


def test_api_report_round_trip_reviews_and_access_denial(database):
    job, chunk = source(database)
    report = draft(database, chunk)
    grant(database)
    database.commit()
    app = create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True)
    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer ' + TOKEN}
        saved = client.post('/api/v1/reports', headers=headers, json=report.model_dump(mode='json'))
        assert saved.status_code == 201
        path = f'/api/v1/reports/{report.report_id}/1'
        assert client.get(path, headers=headers).json()['citations'][0]['source']['text'] == chunk['text']
        assert client.post(path + '/reviews', headers=headers, json={'decision': 'reviewed', 'expected_revision': 0, 'reason': 'Checked it'}).status_code == 201
        assert client.post('/api/v1/reports', headers=headers, json=report.model_dump(mode='json')).status_code == 409
        response = client.post(f"/api/v1/documents/{job['document_id']}/access", headers=headers, json={'blocked': True, 'expected_revision': 0, 'reason': 'Permission withdrawn'})
        assert response.status_code == 200
        assert client.get(path, headers=headers).status_code == 422
        assert client.get(f"/api/v1/documents/{job['document_version_id']}/pdf", headers=headers).status_code == 404


def test_other_department_cannot_read_source_or_correct_payment(database):
    from backend.data.models import AccessContext
    prepare_demo(database, CTX)
    other = AccessContext(actor_id=uuid4())
    database.execute("INSERT INTO data_roles VALUES(%s,'administrator')", (other.actor_id,))
    payment = demo_spending(database, CTX)['payments'][0]
    with pytest.raises(DataError, match='not_found'):
        correct_payment(database, payment['payment_id'], CorrectionInput(expected_classification=payment['classification'], classification='unresolved', reason='Wrong department'), other)
    job, _ = source(database)
    with pytest.raises(DataError, match='not_found'):
        read_document(database, job['document_version_id'], other)
    with pytest.raises(DataError, match='not_found'):
        restrict_document(database, job['document_id'], RestrictionInput(blocked=True, expected_revision=0, reason='Wrong department'), other)


def test_extraction_configuration_creates_new_version(database, monkeypatch):
    from backend.data import ingestion
    from test_week2 import ingest
    first = ingest(database)
    monkeypatch.setattr(ingestion, 'EXTRACTION_VERSION', 'test-new-chunking-config')
    second = ingest(database, document_id=first['document_id'])
    assert first['document_version_id'] != second['document_version_id']
    assert read_document(database, first['document_version_id'], CTX)[1].startswith(b'%PDF')
