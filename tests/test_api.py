"""Yasha's application boundary now uses the authenticated shared API."""

from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.api.main import app as compatibility_app
from backend.api.app import app

TOKEN = "integration-test-only-token"
HEADERS = {"Authorization": "Bearer " + TOKEN}


def no_database():
    raise AssertionError("Invalid/unauthenticated requests must not reach the database")


def test_legacy_entry_point_uses_shared_app():
    assert compatibility_app is app


def test_health_and_authenticated_boundary():
    with TestClient(create_app(no_database, local_mode=True, token=TOKEN)) as client:
        assert client.get("/api/v1/health").json()["status"] == "ok"
        assert client.get("/api/v1/documents").status_code == 401
        assert client.post("/api/v1/assignments/10000000-0000-4000-8000-000000000001/consult").status_code == 401


def test_validation_rejects_legacy_source_keys_and_blank_problem():
    with TestClient(create_app(no_database, local_mode=True, token=TOKEN)) as client:
        response = client.post("/api/v1/assignments", headers=HEADERS, json={
            "problem": "   ", "department_id": "dept-fixture-001",
            "intended_result": "Plan", "selected_document_version_ids": ["doc-fixture-v1"],
        })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_request"
        assert "body.problem" in response.json()["error"]["fields"]
        assert "body.department_id" in response.json()["error"]["fields"]
