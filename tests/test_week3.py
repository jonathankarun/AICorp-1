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
    # basically extra documents and specialties shouldnt make the payment total bigger
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
    # this is another real $100 payment, so we still need to count it even if the amount matches
    database.execute(
        """INSERT INTO payments(payment_id,source_key,vendor_id,engagement_id,amount,currency,paid_on,classification,classification_reason,source_uri,department_id)
        SELECT %s,'week3-equal-payment',vendor_id,engagement_id,100,'USD',paid_on,classification,classification_reason,source_uri,department_id FROM payments LIMIT 1""",
        (uuid4(),),
    )
    result = comparable_work(
        database, ComparableInput(specialty="permit", department_id=DEPT), CTX
    )[0]
    # we should get $400 from 3 payments, with the contract value kept separate
    assert result["payments"] == [
        {"currency": "USD", "transaction_count": 3, "amount": Decimal("400.00")}
    ]
    assert len(result["documents"]) == 2
    assert result["contract_values"][0]["amount"] == Decimal("1000.00")
    assert next(f for f in result["facts"] if f["kind"] == "outcome")["value"] is None
    assert result["match_reasons"] == ["same department", "specialty: permit"]
    # no matching topic or no department access should just give us no results
    assert comparable_work(database, ComparableInput(topic="quasars"), CTX) == []
    assert (
        comparable_work(database, ComparableInput(), AccessContext(actor_id=uuid4()))
        == []
    )


def test_old_citation_survives_source_and_report_revision(database):
    # this checks that an old report still points to the same evidence after we update things
    job, chunk = source(database)
    report = draft(database, chunk)
    identifier = save_report(database, report, CTX)
    # adding a newline changes the PDF bytes so the upload gets a new version
    updated = ingest(database, PDF + b"\n", document_id=job["document_id"])
    assert updated["document_version_id"] != job["document_version_id"]
    report.version = 2
    save_report(database, report, CTX)
    # pull up version 1 again and make sure its source text and original PDF are still there
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
    # trying to delete the saved history should fail
    for table in ["report_versions", "report_citations"]:
        with pytest.raises(psycopg.errors.CheckViolation), database.transaction():
            database.execute(
                f"DELETE FROM {table} WHERE report_version_id=%s", (identifier,)
            )
    # being in the same department doesnt let another user read someone elses report
    with pytest.raises(DataError, match="not_found"):
        get_report(
            database,
            report.report_id,
            1,
            AccessContext(actor_id=uuid4(), allowed_department_ids=(DEPT,)),
        )


def test_bad_citations_leave_no_report(database):
    # give the report a made up source ID and check that it doesnt save
    _, chunk = source(database)
    report = draft(database, chunk)
    report.citations[0].evidence_chunk_id = str(uuid4())
    with pytest.raises(DataError, match="source_not_ready"):
        save_report(database, report, CTX)
    # the error alone isnt enough, there should also be nothing left in the database
    assert database.execute("SELECT count(*) AS n FROM reports").fetchone()["n"] == 0
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 0
    )


def test_report_save_rolls_back_if_citation_insert_fails(database):
    # this checks what happens if saving breaks partway through
    _, chunk = source(database)
    report = draft(database, chunk)
    # force the database to fail on the citation, after the report content was already inserted
    database.execute(
        """CREATE FUNCTION fail_citation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'test citation failure'; END; $$"""
    )
    database.execute(
        "CREATE TRIGGER test_failure BEFORE INSERT ON report_citations FOR EACH ROW EXECUTE FUNCTION fail_citation()"
    )
    with pytest.raises(psycopg.errors.RaiseException, match="test citation failure"):
        save_report(database, report, CTX)
    # the whole save should be undone so we dont end up with half a report
    assert database.execute("SELECT count(*) AS n FROM reports").fetchone()["n"] == 0
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 0
    )


def test_report_rejects_duplicate_version_and_unselected_source(database):
    # save version 1 normally, then make sure we cant save that same version again
    _, chunk = source(database)
    report = draft(database, chunk)
    save_report(database, report, CTX)
    with pytest.raises(DataError, match="report_version_conflict"):
        save_report(database, report, CTX)
    # now try version 2 with a source we never selected for this assignment
    other = ingest(database, title="Not selected")
    other_chunk = database.execute(
        "SELECT chunk_id FROM chunks WHERE document_version_id=%s LIMIT 1",
        (other["document_version_id"],),
    ).fetchone()
    report.version = 2
    report.citations[0].evidence_chunk_id = str(other_chunk["chunk_id"])
    with pytest.raises(DataError, match="citation_outside_assignment"):
        save_report(database, report, CTX)
    # both bad saves should leave just the original version
    assert (
        database.execute("SELECT count(*) AS n FROM report_versions").fetchone()["n"]
        == 1
    )


def test_facts_filter_model_permissions_and_reject_missing_sources(database):
    # this source is allowed internally but isnt allowed to go to an external AI model
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
    # the normal model search should hide it, but the internal search should find it
    assert comparable_work(database, ComparableInput(specialty="hidden"), CTX) == []
    assert comparable_work(
        database, ComparableInput(specialty="hidden", for_external_model=False), CTX
    )
    # we also shouldnt be able to add a fact using a source that doesnt exist
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
    # even with a real source, a user without department access should be blocked
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
    # try a few bad inputs and make sure they get rejected before anything is saved
    base = dict(engagement_id=ENG, evidence_chunk_id=uuid4())
    # missing outcome, blank text, invalid money, too many decimal places, and a link to itself
    for fields in [
        dict(kind="outcome"),
        dict(kind="method", value=" "),
        dict(kind="contract_value", value="ceiling", amount="NaN", currency="USD"),
        dict(kind="contract_value", value="ceiling", amount="1.001", currency="USD"),
        dict(kind="related_engagement", value="same work", related_engagement_id=ENG),
    ]:
        # each set of fields should raise an error when we try to make a FactInput
        with pytest.raises(ValueError):
            FactInput(**base, **fields)


def test_published_week3_contracts_match():
    # the data formats we give teammates should match what the code actually expects
    import json
    from backend.data.db import ROOT

    for name, model in [
        ("fact-input", FactInput),
        ("comparable-input", ComparableInput),
        ("report", Report),
    ]:
        # read the saved JSON format and compare it with the one generated by the model
        assert (
            json.loads(
                (ROOT / "contracts/data/v3" / (name + ".schema.json")).read_text()
            )
            == model.model_json_schema()
        )


def test_competing_report_writers_save_one_version(database):
    # this is like two requests trying to save the same report version at the same time
    from concurrent.futures import ThreadPoolExecutor
    from backend.data.db import connect

    _, chunk = source(database)
    report = draft(database, chunk)
    # save the setup first so both database connections can see it
    database.commit()

    def write():
        # each writer gets its own connection and tells us whether the save worked
        with connect(database.info.dbname) as conn:
            try:
                save_report(conn, report, CTX)
                return "saved"
            except DataError as exc:
                return exc.code

    # run both writers together, only one should get to save this version
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: write(), range(2)))
    assert sorted(outcomes) == ["report_version_conflict", "saved"]
    # then check that the report that did save has the right content
    with connect(database.info.dbname) as conn:
        assert (
            get_report(conn, report.report_id, 1, CTX)["content"]["sections"][0][
                "content"
            ]
            == report.sections[0].content
        )


def test_fact_kinds_and_related_engagement(database):
    # this checks that we can save the different fact types and get them back
    _, chunk = source(database)
    related = uuid4()
    # make a second project so we have something real to link the first project to
    database.execute(
        """INSERT INTO engagements(engagement_id,source_key,department_id,vendor_id,title,source_uri)
        SELECT %s,'week3-related',department_id,vendor_id,'Related fixture work',source_uri FROM engagements WHERE engagement_id=%s""",
        (related, ENG),
    )
    # add the regular facts first, then add the link to the related project
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
    # search for the project and make sure all five fact types came back
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
