"""Week 2 acceptance and regression checks using disposable PostgreSQL databases."""

from io import BytesIO
import json
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from backend.api.app import create_app
from backend.data.db import ROOT, connect, migrate
from backend.data.seed import seed
from backend.data.testing import empty_test_database
from backend.data.models import AccessContext
from backend.data.week2_models import AssignmentInput, DocumentInput, SearchInput
from backend.data.workspace import (
    DataError,
    get_assignment,
    get_job,
    list_documents,
    save_assignment,
)
from backend.data.ingestion import process_job, submit_pdf
from backend.data.importer import import_csv, spending
from backend.data.search import search
from backend.engine.models import Assignment
from backend.engine.pipeline import run_engine
from backend.engine.retrieval import DataEvidenceRepository

FIX = ROOT / "tests/fixtures/week2"
DEPT = UUID("10000000-0000-4000-8000-000000000001")
CTX = AccessContext(
    actor_id=UUID("50000000-0000-4000-8000-000000000001"),
    allowed_department_ids=(DEPT,),
)
MANIFEST = json.loads((FIX / "manifest.json").read_text())
PDF = (FIX / "engagement.pdf").read_bytes()
CSV = (FIX / "payments.csv").read_bytes()
TOKEN = "week2-test-only-token"


@pytest.fixture
def database(request):
    if not request.config.getoption("--run-data"):
        pytest.skip("Use --run-data for PostgreSQL checks")
    with empty_test_database() as conn:
        migrate(conn)
        seed(conn)
        conn.commit()
        yield conn


def metadata(**changes):
    return DocumentInput(**{**MANIFEST["pdf"], **changes})


def ingest(conn, content=PDF, **changes):
    job = submit_pdf(conn, content, metadata(**changes), CTX)
    conn.commit()
    process_job(conn, job)
    conn.commit()
    return get_job(conn, job, CTX)


def assignment(**changes):
    return AssignmentInput(
        **{
            "problem": "Improve permit intake",
            "department_id": DEPT,
            "intended_result": "A preliminary improvement plan",
            **changes,
        }
    )


def test_money_repeat_and_scope(database):
    first = import_csv(database, CSV, MANIFEST)
    second = import_csv(database, CSV, MANIFEST)
    assert first["inserted"] == 5 and not first["rejected"]
    assert second["unchanged"] == 5 and second["inserted"] == 0
    budget = json.loads((FIX / "budget.json").read_text())
    result = spending(
        database,
        department_id=DEPT,
        start="2026-10-01",
        end="2026-10-31",
        budget=budget,
        source_key=MANIFEST["source_key"],
    )
    assert [
        result[k]
        for k in ("consulting", "operational", "unresolved", "consulting_share_percent")
    ] == ["280.00", "500.00", "50.00", "2.80"]
    with pytest.raises(ValueError, match="scope"):
        spending(
            database,
            department_id=DEPT,
            start="2026-09-01",
            end="2026-10-31",
            budget=budget,
            source_key=MANIFEST["source_key"],
        )


def test_rejections_and_traceable_correction(database):
    bad = CSV.replace(b"100.00", b"NaN")
    result = import_csv(database, bad, MANIFEST)
    assert (
        len(result["rejected"]) == 1 and result["rejected"][0]["raw"]["amount"] == "NaN"
    )
    corrected = import_csv(database, CSV, MANIFEST)
    assert corrected["inserted"] == 1
    updated = import_csv(database, CSV.replace(b"100.00", b"110.00"), MANIFEST)
    assert updated["updated"] == 1
    history = database.execute(
        "SELECT old_record,new_record FROM payment_revisions WHERE old_record IS NOT NULL"
    ).fetchone()
    assert (
        history["old_record"]["amount"] == "100.00"
        and history["new_record"]["amount"] == "110.00"
    )
    assert (
        database.execute(
            "SELECT raw_bytes FROM source_imports ORDER BY created_at LIMIT 1"
        ).fetchone()["raw_bytes"]
        == bad
    )


def test_collision_and_legitimate_equal_payments(database):
    header, *rows = CSV.decode().splitlines()
    row = rows[0]
    ambiguous = "\n".join(
        [header, row.replace("p-001,", ","), row.replace("p-001,", ",")]
    ).encode()
    assert len(import_csv(database, ambiguous, MANIFEST)["rejected"]) == 2
    distinct = "\n".join([header, row, row.replace("p-001,", "other-id,")]).encode()
    assert import_csv(database, distinct, MANIFEST)["inserted"] == 2


@pytest.mark.parametrize("replacement", [b"1.001", b"Infinity", b"not-money"])
def test_invalid_money(database, replacement):
    result = import_csv(database, CSV.replace(b"100.00", replacement), MANIFEST)
    assert len(result["rejected"]) == 1


def test_versions_and_page_search(database):
    first = ingest(database)
    assert first["status"] == "ready"
    repeat = ingest(database, document_id=first["document_id"])
    again = ingest(database, document_id=first["document_id"])
    # Same content and metadata reuse even when the follow-up supplies document_id.
    assert (
        first["document_version_id"]
        == repeat["document_version_id"]
        == again["document_version_id"]
    )
    changed = ingest(database, document_id=first["document_id"], title="Revised title")
    assert changed["document_version_id"] != repeat["document_version_id"]
    found = search(
        database,
        SearchInput(
            query="timeline",
            selected_document_version_ids=[first["document_version_id"]],
        ),
        CTX,
    )
    assert found["chunks"][0]["page_number"] == 1
    assert found["chunks"][0]["document_version_id"] == first["document_version_id"]
    assert (
        search(database, SearchInput(query="deliverables"), CTX)["chunks"][0][
            "page_number"
        ]
        == 2
    )
    assert (
        search(database, SearchInput(query="quasars"), CTX)["result_type"]
        == "evidence_gap"
    )
    assert (
        search(
            database,
            SearchInput(query="timeline", selected_document_version_ids=[]),
            CTX,
        )["chunks"]
        == []
    )


def test_failed_documents_have_no_evidence(database):
    corrupt = ingest(database, b"%PDF-1.4\nnot a PDF")
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    out = BytesIO()
    writer.write(out)
    blank = ingest(database, out.getvalue())
    assert corrupt["status"] == blank["status"] == "failed"
    assert (
        corrupt["error_code"] == "unreadable_pdf"
        and blank["error_code"] == "empty_or_scanned_page"
    )
    assert list_documents(database, CTX) == []


def test_assignments_and_authorization(database):
    job = ingest(database)
    saved = save_assignment(
        database,
        assignment(selected_document_version_ids=[job["document_version_id"]]),
        CTX,
    )
    database.commit()
    with connect(database.info.dbname) as other:
        assert get_assignment(other, saved["assignment_id"], CTX)[
            "selected_document_version_ids"
        ] == [str(job["document_version_id"])]
    unauthorized = AccessContext(actor_id=uuid4(), allowed_department_ids=())
    assert list_documents(database, unauthorized) == []
    assert search(database, SearchInput(query="timeline"), unauthorized)["chunks"] == []
    with pytest.raises(DataError):
        get_assignment(database, saved["assignment_id"], unauthorized)
    with pytest.raises(DataError):
        save_assignment(
            database, assignment(selected_document_version_ids=[uuid4()]), CTX
        )
    with pytest.raises(DataError):
        save_assignment(database, assignment(), unauthorized)


class CaptureModel:
    call_count = 0

    def generate(self, assignment, evidence):
        from backend.engine.models import UsageRecord

        self.call_count += 1
        self.evidence = evidence
        return {
            "report_id": str(uuid4()),
            "assignment_id": assignment.assignment_id,
            "version": 1,
            "status": "draft",
            "sections": [
                {"name": "findings", "content": "Fixture response", "citation_ids": []}
            ],
            "citations": [],
        }, UsageRecord(
            provider="mock",
            model="capture",
            prompt_version="v1",
            input_units=0,
            output_units=0,
        )


def test_engine_evidence_permissions_and_gap(database):
    public = ingest(database)
    forbidden = ingest(
        database, title="Readable but no external use", external_model_allowed=False
    )
    model = CaptureModel()
    request = Assignment(
        assignment_id=str(uuid4()),
        problem="permit timeline",
        department_id=str(DEPT),
        intended_result="improvement plan",
        constraints=["six weeks"],
    )
    result = run_engine(request, model, DataEvidenceRepository(database, CTX))
    assert result.result_type == "report" and model.call_count == 1
    assert all(
        e.document_version_id == str(public["document_version_id"])
        for e in model.evidence
    )
    request.selected_document_version_ids = [str(forbidden["document_version_id"])]
    model = CaptureModel()
    result = run_engine(request, model, DataEvidenceRepository(database, CTX))
    assert result.result_type == "needs_input" and model.call_count == 0
    request.selected_document_version_ids = []
    assert DataEvidenceRepository(database, CTX, max_chars=1)(request) == []


def client_for(database, **options):
    return TestClient(
        create_app(
            lambda: connect(database.info.dbname),
            context=CTX,
            token=TOKEN,
            local_mode=True,
            **options,
        )
    )


def test_api_persistence_upload_and_failures(database):
    headers = {"Authorization": "Bearer " + TOKEN}
    with client_for(database) as client:
        assert client.get("/api/v1/documents").status_code == 401
        response = client.post(
            "/api/v1/documents",
            headers=headers,
            data={"metadata": metadata().model_dump_json()},
            files={"file": ("fixture.pdf", PDF, "application/pdf")},
        )
        assert response.status_code == 202 and response.json()["status"] == "pending"
        job = client.get(
            "/api/v1/uploads/" + response.json()["job_id"], headers=headers
        ).json()
        assert job["status"] == "ready"
        data = assignment(
            selected_document_version_ids=[job["document_version_id"]]
        ).model_dump(mode="json")
        saved = client.post("/api/v1/assignments", headers=headers, json=data)
        assert saved.status_code == 201
        identifier = saved.json()["assignment_id"]
        assert (
            client.post(
                "/api/v1/assignments",
                headers=headers,
                json={**data, "created_by": "attacker"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/assignments", headers=headers, json={**data, "problem": "   "}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/documents",
                headers=headers,
                data={"metadata": metadata().model_dump_json()},
                files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
            ).status_code
            == 415
        )
    with client_for(database) as restarted:
        assert restarted.get(
            "/api/v1/assignments/" + identifier, headers=headers
        ).json()["selected_document_version_ids"] == [job["document_version_id"]]
    with client_for(database, max_bytes=10) as limited:
        assert (
            limited.post(
                "/api/v1/documents",
                headers=headers,
                data={"metadata": metadata().model_dump_json()},
                files={"file": ("large.pdf", PDF, "application/pdf")},
            ).status_code
            == 413
        )


def test_api_cannot_self_approve_model_use(database):
    # Valid altered PDF is not the approved fixture hash.
    with client_for(database) as client:
        headers = {"Authorization": "Bearer " + TOKEN}
        response = client.post(
            "/api/v1/documents",
            headers=headers,
            data={"metadata": metadata().model_dump_json()},
            files={"file": ("changed.pdf", PDF + b"\n", "application/pdf")},
        )
        assert response.status_code == 202
        sources = client.get("/api/v1/documents", headers=headers).json()
        assert len(sources) == 1 and not sources[0]["external_model_allowed"]


def test_api_refuses_nonlocal_configuration():
    with pytest.raises(RuntimeError, match="Local API"):
        with TestClient(create_app(local_mode=False, token=TOKEN)):
            pass


def test_exported_week2_contracts_match():
    from backend.data.export_week2_contracts import artifacts

    for name, expected in artifacts().items():
        assert json.loads((ROOT / "contracts/data/v2" / name).read_text()) == expected


def test_interrupted_job_can_resume_and_unknown_access_is_hidden(database):
    identifier = submit_pdf(
        database,
        PDF,
        metadata(access_status="unknown", external_model_allowed=False),
        CTX,
    )
    database.execute(
        "UPDATE ingestion_jobs SET status='processing' WHERE job_id=%s", (identifier,)
    )
    database.commit()
    process_job(database, identifier)
    database.commit()
    assert get_job(database, identifier, CTX)["status"] == "ready"
    assert list_documents(database, CTX) == []
    assert (
        search(database, SearchInput(query="timeline", for_external_model=False), CTX)[
            "chunks"
        ]
        == []
    )


def test_chunk_budget_and_deduplication(database):
    ingest(database)
    ingest(database, title="Duplicate document")
    request = Assignment(
        assignment_id=str(uuid4()),
        department_id=str(DEPT),
        problem="timeline deliverables",
        intended_result="plan",
    )
    evidence = DataEvidenceRepository(database, CTX, max_chars=1200)(request)
    assert evidence and sum(len(e.text) for e in evidence) <= 1200
    assert len({e.text for e in evidence}) == len(evidence)


def test_invalid_shared_ids_return_structured_engine_error(database):
    request = Assignment(
        assignment_id="fixture",
        department_id=str(DEPT),
        problem="timeline",
        intended_result="plan",
        selected_document_version_ids=["doc-fixture-v1"],
    )
    model = CaptureModel()
    result = run_engine(request, model, DataEvidenceRepository(database, CTX))
    assert (
        result.result_type == "error"
        and result.code == "invalid_retrieval_request"
        and model.call_count == 0
    )


def test_unapproved_readable_document_can_be_read_but_not_sent_externally(database):
    ingest(database, external_model_allowed=False)
    assert search(
        database, SearchInput(query="timeline", for_external_model=False), CTX
    )["chunks"]
    assert (
        search(database, SearchInput(query="timeline", for_external_model=True), CTX)[
            "chunks"
        ]
        == []
    )


def test_changed_pdf_preserves_old_chunks(database):
    job = ingest(database)
    old = database.execute(
        "SELECT * FROM chunks WHERE document_version_id=%s",
        (job["document_version_id"],),
    ).fetchall()
    changed = ingest(database, PDF + b"\n", document_id=job["document_id"])
    assert changed["document_version_id"] != job["document_version_id"]
    assert (
        database.execute(
            "SELECT * FROM chunks WHERE document_version_id=%s",
            (job["document_version_id"],),
        ).fetchall()
        == old
    )


def test_same_job_concurrent_workers_create_one_version(database):
    from concurrent.futures import ThreadPoolExecutor

    identifier = submit_pdf(database, PDF, metadata(), CTX)
    database.commit()

    def work():
        with connect(database.info.dbname) as conn:
            return process_job(conn, identifier)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: work(), range(2))) == ["ready", "ready"]
    assert (
        database.execute("SELECT count(*) AS n FROM document_versions").fetchone()["n"]
        == 1
    )


def test_engine_respects_assignment_department_even_if_actor_can_read_both(database):
    ingest(database)
    other = uuid4()
    broad = AccessContext(actor_id=CTX.actor_id, allowed_department_ids=(DEPT, other))
    request = Assignment(
        assignment_id=str(uuid4()),
        department_id=str(other),
        problem="timeline",
        intended_result="plan",
    )
    assert DataEvidenceRepository(database, broad)(request) == []
