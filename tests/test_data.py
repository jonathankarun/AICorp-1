"""Real PostgreSQL checks. Run: python -m pytest --run-data -q"""
from copy import deepcopy
from decimal import Decimal
import json
from uuid import UUID, uuid4

import psycopg
import pytest

from backend.data import db, seed as seed_module
from backend.data.models import AccessContext
from backend.data.repository import DataRepository
from backend.data.seed import load_fixture, seed
from backend.data.testing import empty_test_database
from backend.data.validate import validate_database


@pytest.fixture
def empty_db(request):
    if not request.config.getoption("--run-data"):
        pytest.skip("PostgreSQL integration: run setup, then pytest --run-data")
    with empty_test_database() as conn:
        yield conn


@pytest.fixture
def seeded_db(empty_db):
    db.migrate(empty_db)
    seed(empty_db)
    return empty_db


def insert_payment(conn, *, vendor=None, engagement="30000000-0000-4000-8000-000000000001", amount="1.00"):
    conn.execute("""
        INSERT INTO payments (payment_id, source_key, vendor_id, engagement_id,
            amount, currency, paid_on, classification, classification_reason, source_uri)
        VALUES (%s, %s, %s, %s, %s, 'USD', '2026-09-29', 'unresolved',
            'Test-only unknown service', 'fixture://test-payment')
    """, (uuid4(), str(uuid4()), UUID(vendor or "20000000-0000-4000-8000-000000000001"), UUID(engagement) if engagement else None, Decimal(amount)))


def test_full_week1_acceptance_in_empty_database(empty_db):
    checks = []
    result = validate_database(empty_db, checks)
    assert all(item["passed"] for item in checks)
    assert result["lookup"]["engagement"]["vendor"]["name"] == "Fictional Process Consulting LLC"
    expected = json.loads((db.ROOT / "contracts/data/v1/engagement-found.example.json").read_text())
    assert result["lookup"] == expected


def test_seed_keeps_ids_and_amounts_identical(seeded_db):
    before = seeded_db.execute("SELECT * FROM payments ORDER BY payment_id").fetchall()
    seed(seeded_db)
    after = seeded_db.execute("SELECT * FROM payments ORDER BY payment_id").fetchall()
    assert before == after


def test_seed_conflict_rolls_back_partial_insert(seeded_db, monkeypatch):
    # Remove the first fixture payment; then the seed will insert it before hitting
    # a deliberate amount conflict on the second. The entire seed must roll back.
    seeded_db.execute("DELETE FROM payments WHERE source_key = 'payment-fixture-001'")
    changed = deepcopy(load_fixture())
    changed["payments"][1]["amount"] = "201.00"
    monkeypatch.setattr(seed_module, "load_fixture", lambda: changed)
    with pytest.raises(ValueError, match="Seed conflict"):
        seed(seeded_db)
    rows = seeded_db.execute("SELECT source_key, amount FROM payments").fetchall()
    assert rows == [{"source_key": "payment-fixture-002", "amount": Decimal("200.00")}]


def test_migration_checksum_detects_changed_history(seeded_db, monkeypatch, tmp_path):
    source = db.MIGRATIONS / "001_initial.sql"
    (tmp_path / source.name).write_text(source.read_text() + "\n-- changed\n")
    monkeypatch.setattr(db, "MIGRATIONS", tmp_path)
    with pytest.raises(ValueError, match="Applied migration changed"):
        db.migrate(seeded_db)


def test_failed_migration_rolls_back_schema(empty_db, monkeypatch, tmp_path):
    (tmp_path / "001_broken.sql").write_text("CREATE TABLE should_rollback (id integer); SELECT * FROM missing_table;")
    monkeypatch.setattr(db, "MIGRATIONS", tmp_path)
    with pytest.raises(psycopg.errors.UndefinedTable):
        db.migrate(empty_db)
    assert empty_db.execute("SELECT to_regclass('public.should_rollback') AS name").fetchone()["name"] is None


def test_unknown_vendor_rejected(seeded_db):
    with pytest.raises(psycopg.errors.ForeignKeyViolation), seeded_db.transaction():
        insert_payment(seeded_db, vendor=str(uuid4()), engagement=None)


def test_payment_cannot_disagree_with_engagement_vendor(seeded_db):
    other = uuid4()
    seeded_db.execute("INSERT INTO vendors VALUES (%s, 'other-vendor', 'Other fixture', 'fixture://other')", (other,))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), seeded_db.transaction():
        insert_payment(seeded_db, vendor=str(other))


def test_unknown_engagement_can_remain_null(seeded_db):
    insert_payment(seeded_db, engagement=None)
    row = seeded_db.execute("SELECT engagement_id, classification FROM payments WHERE engagement_id IS NULL").fetchone()
    assert row == {"engagement_id": None, "classification": "unresolved"}


def test_refunds_use_exact_decimal_without_float(seeded_db):
    # Validates the schema permits future refunds; does not alter the seed fixture.
    insert_payment(seeded_db, amount="-20.00")
    result = seeded_db.execute("SELECT sum(amount) AS total FROM payments").fetchone()["total"]
    assert isinstance(result, Decimal)
    assert result == Decimal("280.00")


def test_nan_money_is_rejected(seeded_db):
    with pytest.raises(psycopg.errors.CheckViolation), seeded_db.transaction():
        insert_payment(seeded_db, amount="NaN")


def test_other_department_context_cannot_lookup(seeded_db):
    ctx = AccessContext(actor_id=uuid4(), allowed_department_ids=(uuid4(),))
    result = DataRepository(seeded_db).get_engagement(load_fixture()["engagement"]["engagement_id"], ctx)
    assert result.result_type == "not_found"


def test_invalid_uuid_cannot_be_used_as_sql(seeded_db):
    with pytest.raises(ValueError):
        DataRepository(seeded_db).get_engagement("' OR 1=1 --", AccessContext(actor_id=uuid4()))


def insert_document(conn):
    version_id = uuid4()
    conn.execute("""
        INSERT INTO document_versions (document_version_id, document_id, version,
            title, source_uri, content_hash)
        VALUES (%s, %s, 1, 'Synthetic metadata test', 'fixture://document', %s)
    """, (version_id, uuid4(), "a" * 64))
    return version_id


def test_document_provenance_defaults_deny_external_use(seeded_db):
    version_id = insert_document(seeded_db)
    row = seeded_db.execute("SELECT access_status, external_model_allowed, engagement_id, issuer, published_on FROM document_versions WHERE document_version_id = %s", (version_id,)).fetchone()
    assert row == {"access_status": "unknown", "external_model_allowed": False, "engagement_id": None, "issuer": None, "published_on": None}


def test_chunk_requires_existing_document_version(seeded_db):
    with pytest.raises(psycopg.errors.ForeignKeyViolation), seeded_db.transaction():
        seeded_db.execute("INSERT INTO chunks VALUES (%s, %s, 0, 1, 'Fixture text', %s)", (uuid4(), uuid4(), "b" * 64))


def test_old_evidence_cannot_be_overwritten(seeded_db):
    version_id = insert_document(seeded_db)
    chunk_id = uuid4()
    seeded_db.execute("INSERT INTO chunks VALUES (%s, %s, 0, 1, 'Fixture text', %s)", (chunk_id, version_id, "b" * 64))
    with pytest.raises(psycopg.errors.CheckViolation), seeded_db.transaction():
        seeded_db.execute("UPDATE document_versions SET title = 'Changed' WHERE document_version_id = %s", (version_id,))
    with pytest.raises(psycopg.errors.CheckViolation), seeded_db.transaction():
        seeded_db.execute("UPDATE chunks SET text = 'Changed' WHERE chunk_id = %s", (chunk_id,))
    assert seeded_db.execute("SELECT text FROM chunks WHERE chunk_id = %s", (chunk_id,)).fetchone()["text"] == "Fixture text"
