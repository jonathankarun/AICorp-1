"""Validation must report failures honestly and preserve the working records."""
from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.data.db import connect
from backend.data.demo import prepare_demo
from backend.data import demo_validation
from test_week2 import database, CTX, TOKEN


def client_for(database):
    return TestClient(create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True))


def test_validation_passes_and_preserves_records(database):
    prepare_demo(database, CTX)
    before = demo_validation.record_fingerprints(database)
    with client_for(database) as client:
        assert client.post('/api/v1/demo/validate').status_code == 401
        response = client.post('/api/v1/demo/validate', headers={'Authorization': 'Bearer ' + TOKEN})
        assert response.status_code == 200, response.text
        report = response.json()
        assert report['status'] == 'PASS', report
        assert report['passed'] == report['total'] == 15
        assert report['duration_ms'] >= 0
        assert any(c['name'] == 'Unauthorized correction denied' and c['actual'] == '403 review_permission_required' for c in report['checks'])
        assert demo_validation.record_fingerprints(database) == before
        database.execute('DELETE FROM data_roles WHERE actor_id=%s', (CTX.actor_id,))
        database.commit()
        assert client.post('/api/v1/demo/validate', headers={'Authorization': 'Bearer ' + TOKEN}).status_code == 403


def test_validation_exposes_wrong_result(database, monkeypatch):
    prepare_demo(database, CTX)
    real = demo_validation.run_guided_demo
    def wrong_total(*args):
        result = real(*args)
        result['before']['consulting'] = '999.00'
        return result
    monkeypatch.setattr(demo_validation, 'run_guided_demo', wrong_total)
    with client_for(database) as client:
        report = client.post('/api/v1/demo/validate', headers={'Authorization': 'Bearer ' + TOKEN}).json()
        assert report['status'] == 'FAIL'
        check = next(c for c in report['checks'] if c['name'] == 'Initial spending')
        assert check['status'] == 'FAIL'
        assert check['expected']['consulting'] == '280.00'
        assert check['actual']['consulting'] == '999.00'


def test_validation_reports_error_and_skips_dependent_checks(database, monkeypatch):
    prepare_demo(database, CTX)
    before = demo_validation.record_fingerprints(database)
    def broken(*args):
        raise RuntimeError('Internal detail must not be exposed')
    monkeypatch.setattr(demo_validation, 'run_guided_demo', broken)
    with client_for(database) as client:
        response = client.post('/api/v1/demo/validate', headers={'Authorization': 'Bearer ' + TOKEN})
        report = response.json()
        assert response.status_code == 200
        assert report['status'] == 'FAIL'
        assert any(c['status'] == 'ERROR' for c in report['checks'])
        assert any(c['status'] == 'SKIP' for c in report['checks'])
        assert 'Internal detail' not in response.text
        assert demo_validation.record_fingerprints(database) == before
