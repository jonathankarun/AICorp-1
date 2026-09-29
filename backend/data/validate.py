"""One-command Week 1 demonstration against a newly created PostgreSQL database."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from uuid import UUID

import psycopg
from psycopg import sql

from .db import ROOT, migrate
from .models import AccessContext
from .repository import DataRepository
from .seed import FIXTURE_PATH, load_fixture, seed
from .testing import empty_test_database


def validate_database(conn, checks: list[dict]) -> dict:
    """Run exact checks; raise on the first mismatch and retain failed evidence."""
    def check(name, actual, expected):
        passed = actual == expected
        checks.append({"check": name, "expected": expected, "actual": actual, "passed": passed})
        if not passed:
            raise ValueError(f"Validation failed: {name}")

    tables = ("departments", "vendors", "engagements", "payments", "document_versions", "chunks")

    def counts():
        return {table: conn.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))).fetchone()["n"] for table in tables}

    check("empty_database", conn.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema = 'public'").fetchone()["n"], 0)
    check("first_migration", migrate(conn), ["001_initial.sql"])
    check("first_seed", seed(conn), {"departments": 1, "vendors": 1, "engagements": 1, "payments": 2})
    expected_counts = {"departments": 1, "vendors": 1, "engagements": 1, "payments": 2, "document_versions": 0, "chunks": 0}
    check("first_counts", counts(), expected_counts)
    check("second_seed", seed(conn), {"departments": 0, "vendors": 0, "engagements": 0, "payments": 0})
    check("second_counts", counts(), expected_counts)
    check("second_migration", migrate(conn), [])
    rows = conn.execute("SELECT payment_id, amount, currency FROM payments ORDER BY source_key").fetchall()
    check("payment_values", [format(row["amount"], ".2f") for row in rows], ["100.00", "200.00"])
    check("payment_currencies", [row["currency"] for row in rows], ["USD", "USD"])
    total = conn.execute("SELECT sum(amount) AS total FROM payments WHERE currency = 'USD'").fetchone()["total"]
    check("exact_decimal_type", isinstance(total, Decimal), True)
    check("payment_total_usd", str(total), "300.00")

    fixture = load_fixture()
    engagement_id = fixture["engagement"]["engagement_id"]
    allowed = AccessContext(actor_id=UUID("50000000-0000-4000-8000-000000000001"), allowed_department_ids=(UUID(fixture["department"]["department_id"]),))
    repo = DataRepository(conn)
    found = repo.get_engagement(engagement_id, allowed)
    check("lookup_result", found.result_type, "engagement")
    check("linked_vendor", str(found.engagement.vendor.vendor_id), fixture["vendor"]["vendor_id"])
    check("linked_department", str(found.engagement.department.department_id), fixture["department"]["department_id"])
    missing = repo.get_engagement("30000000-0000-4000-8000-000000000099", allowed)
    check("unknown_engagement", missing.result_type, "not_found")
    hidden = repo.get_engagement(engagement_id, AccessContext(actor_id=allowed.actor_id))
    check("unpermitted_engagement", hidden.result_type, "not_found")
    check("hidden_result_message", hidden.message, missing.message)

    sqlstate = None
    try:
        with conn.transaction():
            conn.execute("""
                INSERT INTO payments (payment_id, source_key, vendor_id, engagement_id,
                    amount, currency, paid_on, classification, classification_reason, source_uri)
                VALUES (%s, 'invalid-fk-fixture', %s, %s, 1.00, 'USD', '2026-09-29',
                    'unresolved', 'Deliberately invalid test', 'fixture://invalid-fk')
            """, (UUID("40000000-0000-4000-8000-000000000099"), UUID(fixture["vendor"]["vendor_id"]), UUID("30000000-0000-4000-8000-000000000099")))
    except psycopg.errors.ForeignKeyViolation as exc:
        sqlstate = exc.sqlstate
    check("invalid_foreign_key_rejected", sqlstate, "23503")
    check("counts_after_rejected_insert", counts(), expected_counts)
    return {
        "lookup": found.model_dump(mode="json"),
        "missing_lookup": missing.model_dump(mode="json"),
        "denied_lookup": hidden.model_dump(mode="json"),
    }


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    paths = sorted((ROOT / "backend/data").rglob("*.py")) + sorted((ROOT / "backend/data/migrations").glob("*.sql")) + [FIXTURE_PATH, ROOT / "requirements.lock"]
    for path in paths:
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/local/week1-validation.json")
    args = parser.parse_args()
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
    record = {
        "fixture_version": load_fixture()["fixture_version"],
        "synthetic": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": revision.stdout.strip() if revision.returncode == 0 else "unavailable",
        "source_sha256": source_fingerprint(),
        "python_version": platform.python_version(),
        "platform": platform.system() + " " + platform.machine(),
        "command": "python -m backend.data.validate",
        "checks": [],
    }
    try:
        with empty_test_database() as conn:
            record["postgresql_version"] = conn.execute("SHOW server_version").fetchone()["server_version"]
            record.update(validate_database(conn, record["checks"]))
        record["test_database_removed"] = True
        record["passed"] = True
    except (ValueError, psycopg.Error) as exc:
        record["passed"] = False
        record["error"] = {"type": type(exc).__name__, "message": "Validation failed; inspect checks, database availability, and setup instructions."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

