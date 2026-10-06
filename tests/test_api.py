"""Deterministic Week 1 API checks for Yasha's application boundary."""

from fastapi.testclient import TestClient

from backend.api.main import app, repository

client = TestClient(app)

VALID_ASSIGNMENT = {
    "problem": "Create a preliminary improvement plan for a fictional city department whose intake process is inconsistent and slow.",
    "department_id": "dept-fixture-001",
    "intended_result": "Provide a reviewable draft plan that improves intake consistency and turnaround time.",
    "required_sections": [
        "problem_summary",
        "findings",
        "recommendation",
        "implementation_steps",
    ],
    "audience": "City department manager",
    "constraints": [
        "Use a six-week implementation horizon",
        "Use only the synthetic fixture evidence",
    ],
    "selected_document_version_ids": ["doc-fixture-v1"],
    "request_type": "problem",
}


def setup_function() -> None:
    repository.clear()


def test_health_endpoint_returns_fixed_success() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_valid_assignment_returns_id_and_normalized_data() -> None:
    response = client.post("/api/v1/assignments", json=VALID_ASSIGNMENT)

    assert response.status_code == 201
    body = response.json()
    assert body["assignment_id"]
    assert body["schema_version"] == "1.0"
    assert body["problem"] == VALID_ASSIGNMENT["problem"]
    assert body["intended_result"] == VALID_ASSIGNMENT["intended_result"]
    assert body["constraints"] == VALID_ASSIGNMENT["constraints"]
    assert body["created_by"] == "local-demo-user"
    assert len(repository.assignments) == 1


def test_whitespace_problem_is_rejected_and_creates_nothing() -> None:
    bad_payload = {**VALID_ASSIGNMENT, "problem": "   "}
    response = client.post("/api/v1/assignments", json=bad_payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert any(field["field"] == "problem" for field in response.json()["error"]["fields"])
    assert len(repository.assignments) == 0
