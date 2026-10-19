# this file checks week 3 against a real disposable database
# the main checks are unchanged payment totals, all-or-nothing saves, and old citations staying readable
from uuid import uuid4
from decimal import Decimal
import pytest
import psycopg
from backend.data.week3_models import FactInput, ComparableInput
from backend.data.history import add_fact, comparable_work, link_document
from backend.data.reports import save_report, get_report
from backend.data.workspace import save_assignment, DataError
from backend.data.models import AccessContext
from backend.engine.models import Report
from test_week2 import database, ingest, assignment, CTX, DEPT, PDF

ENG = "30000000-0000-4000-8000-000000000001"


def source(conn):
    job = ingest(conn)
    chunk = conn.execute(
        "SELECT * FROM chunks WHERE document_version_id=%s ORDER BY ordinal",
        (job["document_version_id"],),
    ).fetchone()
    return job, chunk


def draft(conn, chunk):
    saved = save_assignment(
        conn,
        assignment(selected_document_version_ids=[chunk["document_version_id"]]),
        CTX,
    )
    return Report(
        report_id=str(uuid4()),
        assignment_id=str(saved["assignment_id"]),
        sections=[
            {
                "name": "findings",
                "content": "Fictional six-week timeline.",
                "citation_ids": ["c1"],
            }
        ],
        citations=[{"citation_id": "c1", "evidence_chunk_id": str(chunk["chunk_id"])}],
    )


def test_comparables_do_not_multiply_equal_payments(database):
    first, chunk = source(database)
    second = ingest(database, title="Another fictional source")
    for name in ["process improvement", "permit intake"]:
        add_fact(
            database,
            FactInput(
                engagement_id=ENG,
                kind="specialty",
                value=name,
                evidence_chunk_id=chunk["chunk_id"],
            ),
            CTX,
        )
    add_fact(
        database,
        FactInput(
            engagement_id=ENG,
            kind="outcome",
            unknown_reason="No measured outcome in this source",
            evidence_chunk_id=chunk["chunk_id"],
        ),
        CTX,
    )
    add_fact(
        database,
        FactInput(
            engagement_id=ENG,
            kind="contract_value",
            value="Fictional contract ceiling",
            amount="1000.00",
            currency="USD",
            evidence_chunk_id=chunk["chunk_id"],
        ),
        CTX,
    )
    link_document(database, ENG, second["document_version_id"], CTX)
    # this adds a separate $100 payment so SUM(DISTINCT amount) would give the wrong answer
    database.execute(
        """INSERT INTO payments(payment_id,source_key,vendor_id,engagement_id,amount,currency,paid_on,classification,classification_reason,source_uri,department_id)
        SELECT %s,'week3-equal-payment',vendor_id,engagement_id,100,'USD',paid_on,classification,classification_reason,source_uri,department_id FROM payments LIMIT 1""",
        (uuid4(),),
    )
    result = comparable_work(
        database, ComparableInput(specialty="permit", department_id=DEPT), CTX
    )[0]
    assert result["payments"] == [
        {"currency": "USD", "transaction_count": 3, "amount": Decimal("400.00")}
    ]
    assert len(result["documents"]) == 2
    assert result["contract_values"][0]["amount"] == Decimal("1000.00")
    assert next(f for f in result["facts"] if f["kind"] == "outcome")["value"] is None
    assert result["match_reasons"] == ["same department", "specialty: permit"]
    assert comparable_work(database, ComparableInput(topic="quasars"), CTX) == []
    assert (
        comparable_work(database, ComparableInput(), AccessContext(actor_id=uuid4()))
        == []
    )


def test_old_citation_survives_source_and_report_revision(database):
    job, chunk = source(database)
    report = draft(database, chunk)
    identifier = save_report(database, report, CTX)
    updated = ingest(database, PDF + b"\n", document_id=job["document_id"])
    assert updated["document_version_id"] != job["document_version_id"]
    report.version = 2
    save_report(database, report, CTX)
    old = get_report(database, report.report_id, 1, CTX)
    assert old["report_version_id"] == identifier
    assert (
        old["citations"][0]["source"]["document_version_id"]
        == job["document_version_id"]
    )
    assert old["citations"][0]["source"]["text"] == chunk["text"]
    assert (
        bytes(
            database.execute(
                "SELECT raw_bytes FROM ingestion_jobs WHERE job_id=%s", (job["job_id"],)
            ).fetchone()["raw_bytes"]
        )
        == PDF
    )
    for table in ["report_versions", "report_citations"]:
        with pytest.raises(psycopg.errors.CheckViolation), database.transaction():
            database.execute(
                f"DELETE FROM {table} WHERE report_version_id=%s", (identifier,)
            )
    with pytest.raises(DataError, match="not_found"):
        get_report(
            database,
            report.report_id,
            1,
            AccessContext(actor_id=uuid4(), allowed_department_ids=(DEPT,)),
        )


def test_bad_citations_leave_no_report(database):
    _, chunk = source(database)
    report = draft(database, chunk)
    report.citations[0].evidence_chunk_id = str(uuid4())
    with pytest.raises(DataError, match="source_not_ready"):
        save_report(database, report, CTX)
    assert database.execute("SELECT count(*) AS n FROM reports").fetchone()["n"] == 0
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 0
    )


def test_report_save_rolls_back_if_citation_insert_fails(database):
    _, chunk = source(database)
    report = draft(database, chunk)
    # this simulates a database failure after the report content has already been inserted
    database.execute(
        """CREATE FUNCTION fail_citation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'test citation failure'; END; $$"""
    )
    database.execute(
        "CREATE TRIGGER test_failure BEFORE INSERT ON report_citations FOR EACH ROW EXECUTE FUNCTION fail_citation()"
    )
    with pytest.raises(psycopg.errors.RaiseException, match="test citation failure"):
        save_report(database, report, CTX)
    assert database.execute("SELECT count(*) AS n FROM reports").fetchone()["n"] == 0
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 0
    )


def test_report_rejects_duplicate_version_and_unselected_source(database):
    _, chunk = source(database)
    report = draft(database, chunk)
    save_report(database, report, CTX)
    with pytest.raises(DataError, match="report_version_conflict"):
        save_report(database, report, CTX)
    other = ingest(database, title="Not selected")
    other_chunk = database.execute(
        "SELECT chunk_id FROM chunks WHERE document_version_id=%s LIMIT 1",
        (other["document_version_id"],),
    ).fetchone()
    report.version = 2
    report.citations[0].evidence_chunk_id = str(other_chunk["chunk_id"])
    with pytest.raises(DataError, match="citation_outside_assignment"):
        save_report(database, report, CTX)
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 1
    )


def test_facts_filter_model_permissions_and_reject_missing_sources(database):
    job = ingest(database, external_model_allowed=False)
    chunk = database.execute(
        "SELECT * FROM chunks WHERE document_version_id=%s LIMIT 1",
        (job["document_version_id"],),
    ).fetchone()
    add_fact(
        database,
        FactInput(
            engagement_id=ENG,
            kind="specialty",
            value="hidden specialty",
            evidence_chunk_id=chunk["chunk_id"],
        ),
        CTX,
    )
    assert comparable_work(database, ComparableInput(specialty="hidden"), CTX) == []
    assert comparable_work(
        database, ComparableInput(specialty="hidden", for_external_model=False), CTX
    )
    with pytest.raises(DataError):
        add_fact(
            database,
            FactInput(
                engagement_id=ENG,
                kind="method",
                value="test",
                evidence_chunk_id=uuid4(),
            ),
            CTX,
        )
    with pytest.raises(DataError):
        add_fact(
            database,
            FactInput(
                engagement_id=ENG,
                kind="method",
                value="test",
                evidence_chunk_id=chunk["chunk_id"],
            ),
            AccessContext(actor_id=uuid4()),
        )


def test_fact_validation():
    base = dict(engagement_id=ENG, evidence_chunk_id=uuid4())
    for fields in [
        dict(kind="outcome"),
        dict(kind="method", value=" "),
        dict(kind="contract_value", value="ceiling", amount="NaN", currency="USD"),
        dict(kind="contract_value", value="ceiling", amount="1.001", currency="USD"),
        dict(kind="related_engagement", value="same work", related_engagement_id=ENG),
    ]:
        with pytest.raises(ValueError):
            FactInput(**base, **fields)


def test_published_week3_contracts_match():
    import json
    from backend.data.db import ROOT

    for name, model in [
        ("fact-input", FactInput),
        ("comparable-input", ComparableInput),
        ("report", Report),
    ]:
        assert (
            json.loads(
                (ROOT / "contracts/data/v3" / (name + ".schema.json")).read_text()
            )
            == model.model_json_schema()
        )


def test_competing_report_writers_save_one_version(database):
    from concurrent.futures import ThreadPoolExecutor
    from backend.data.db import connect

    _, chunk = source(database)
    report = draft(database, chunk)
    database.commit()

    def write():
        with connect(database.info.dbname) as conn:
            try:
                save_report(conn, report, CTX)
                return "saved"
            except DataError as exc:
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: write(), range(2)))
    assert sorted(outcomes) == ["report_version_conflict", "saved"]
    with connect(database.info.dbname) as conn:
        assert (
            get_report(conn, report.report_id, 1, CTX)["content"]["sections"][0][
                "content"
            ]
            == report.sections[0].content
        )


def test_fact_kinds_and_related_engagement(database):
    _, chunk = source(database)
    related = uuid4()
    database.execute(
        """INSERT INTO engagements(engagement_id,source_key,department_id,vendor_id,title,source_uri)
        SELECT %s,'week3-related',department_id,vendor_id,'Related fixture work',source_uri FROM engagements WHERE engagement_id=%s""",
        (related, ENG),
    )
    for kind in ["method", "deliverable", "recommendation", "outcome"]:
        add_fact(
            database,
            FactInput(
                engagement_id=ENG,
                kind=kind,
                value="Fictional assertion for storage checks",
                evidence_chunk_id=chunk["chunk_id"],
            ),
            CTX,
        )
    add_fact(
        database,
        FactInput(
            engagement_id=ENG,
            kind="related_engagement",
            value="Fictional related work",
            related_engagement_id=related,
            evidence_chunk_id=chunk["chunk_id"],
        ),
        CTX,
    )
    case = comparable_work(database, ComparableInput(topic="Fictional assertion"), CTX)[
        0
    ]
    assert {f["kind"] for f in case["facts"]} == {
        "method",
        "deliverable",
        "recommendation",
        "outcome",
        "related_engagement",
    }
