"""CSV staging, exact money, conservative identity matching, and revision history."""

import csv
import hashlib
import io
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from psycopg.types.json import Jsonb

REQUIRED = {
    "transaction_id",
    "vendor",
    "department",
    "engagement_id",
    "amount",
    "currency",
    "paid_on",
    "classification",
    "rationale",
}


def clean_row(conn, row, source):
    if None in row or any(value is None for value in row.values()):
        raise ValueError("Wrong column count")
    r = {key: value.strip() for key, value in row.items()}
    vendor = conn.execute(
        "SELECT vendor_id FROM vendors WHERE lower(name)=lower(%s) OR source_key=%s",
        (r["vendor"], r["vendor"]),
    ).fetchall()
    department = conn.execute(
        "SELECT department_id FROM departments WHERE lower(name)=lower(%s) OR source_key=%s",
        (r["department"], r["department"]),
    ).fetchall()
    if len(vendor) != 1 or len(department) != 1:
        raise ValueError("Unknown or ambiguous vendor/department; review alias")
    amount = Decimal(r["amount"])
    if (
        not amount.is_finite()
        or amount != amount.quantize(Decimal(".01"))
        or abs(amount) >= Decimal("1e16")
    ):
        raise ValueError("Amount must be finite with at most two decimal places")
    amount = amount.quantize(Decimal(".01"))
    paid_on = date.fromisoformat(r["paid_on"])
    if r["currency"] != "USD":
        raise ValueError("Fixture importer supports USD only")
    if (
        r["classification"] not in ("consulting", "operational", "unresolved")
        or not r["rationale"]
    ):
        raise ValueError("Classification and rationale required")
    engagement = UUID(r["engagement_id"]) if r["engagement_id"] else None
    if engagement:
        match = conn.execute(
            "SELECT vendor_id,department_id FROM engagements WHERE engagement_id=%s",
            (engagement,),
        ).fetchone()
        if not match or match != {**vendor[0], **department[0]}:
            raise ValueError("Engagement does not match vendor/department")
    record = {
        "vendor_id": str(vendor[0]["vendor_id"]),
        "department_id": str(department[0]["department_id"]),
        "engagement_id": str(engagement) if engagement else None,
        "amount": str(amount),
        "currency": "USD",
        "paid_on": paid_on.isoformat(),
        "classification": r["classification"],
        "classification_reason": r["rationale"],
        "source_uri": source["location"],
    }
    # No transaction ID: conservative composite, collisions require human review.
    fallback = "|".join(
        [
            record["vendor_id"],
            record["department_id"],
            record["paid_on"],
            record["amount"],
            record["currency"],
            str(record["engagement_id"]),
        ]
    )
    key = (
        source["source_key"]
        + ":"
        + (
            r["transaction_id"]
            or "fallback:" + hashlib.sha256(fallback.encode()).hexdigest()
        )
    )
    return key, record, not bool(r["transaction_id"])


def import_csv(conn, raw: bytes, manifest: dict):
    for key in (
        "source_key",
        "title",
        "issuer",
        "date",
        "location",
        "fiscal_period",
        "access_status",
    ):
        if key not in manifest:
            raise ValueError(f"Manifest missing {key}; use null for unknown attributes")
    if (
        not isinstance(manifest["source_key"], str)
        or not re.fullmatch(r"[A-Za-z0-9._-]+", manifest["source_key"])
        or not manifest["location"]
    ):
        raise ValueError(
            "Use a nonblank location and an alphanumeric/dot/underscore/hyphen source_key"
        )
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if set(reader.fieldnames or []) != REQUIRED:
        raise ValueError("CSV headers must match the published contract")
    rows = list(reader)
    staged = []
    for number, row in enumerate(rows, 2):
        try:
            key, record, fallback = clean_row(conn, row, manifest)
            staged.append((number, row, key, record, fallback, None))
        except (ValueError, InvalidOperation) as exc:
            staged.append((number, row, None, None, False, str(exc)))
    counts = Counter(item[2] for item in staged if item[2])
    import_id = uuid4()
    result = {
        "import_id": str(import_id),
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "rejected": [],
    }
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(2026100501)")
        conn.execute(
            "INSERT INTO source_imports(import_id,source_key,content_hash,manifest,raw_bytes) VALUES(%s,%s,%s,%s,%s)",
            (
                import_id,
                manifest["source_key"],
                hashlib.sha256(raw).hexdigest(),
                Jsonb(manifest),
                raw,
            ),
        )
        for number, row, key, record, fallback, error in staged:
            identifier = None
            if key and counts[key] > 1:
                error = "Duplicate/ambiguous transaction identity within file; review both rows"
            if not error:
                existing = conn.execute(
                    "SELECT * FROM payments WHERE source_key=%s", (key,)
                ).fetchone()
                old = (
                    {
                        k: str(existing[k]) if existing[k] is not None else None
                        for k in record
                    }
                    if existing
                    else None
                )
                if existing and fallback and old != record:
                    error = "Ambiguous fallback correction; supply an explicit transaction ID after review"
                else:
                    identifier = (
                        existing["payment_id"]
                        if existing
                        else uuid5(NAMESPACE_URL, key)
                    )
                    if old == record:
                        outcome = "unchanged"
                    else:
                        outcome = "updated" if existing else "inserted"
                        conn.execute(
                            """INSERT INTO payments(payment_id,source_key,vendor_id,department_id,engagement_id,
                          amount,currency,paid_on,classification,classification_reason,source_uri)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                          ON CONFLICT(source_key) DO UPDATE SET vendor_id=excluded.vendor_id,department_id=excluded.department_id,
                          engagement_id=excluded.engagement_id,amount=excluded.amount,currency=excluded.currency,
                          paid_on=excluded.paid_on,classification=excluded.classification,
                          classification_reason=excluded.classification_reason,source_uri=excluded.source_uri""",
                            (
                                identifier,
                                key,
                                record["vendor_id"],
                                record["department_id"],
                                record["engagement_id"],
                                record["amount"],
                                record["currency"],
                                record["paid_on"],
                                record["classification"],
                                record["classification_reason"],
                                record["source_uri"],
                            ),
                        )
                        conn.execute(
                            "INSERT INTO payment_revisions(payment_id,import_id,old_record,new_record) VALUES(%s,%s,%s,%s)",
                            (
                                identifier,
                                import_id,
                                Jsonb(old) if old else None,
                                Jsonb(record),
                            ),
                        )
                    result[outcome] += 1
            if error:
                outcome = "rejected"
                result["rejected"].append({"row": number, "reason": error, "raw": row})
            conn.execute(
                "INSERT INTO import_rows VALUES(%s,%s,%s,%s,%s,%s)",
                (import_id, number, Jsonb(row), outcome, error, identifier),
            )
    return result


def spending(conn, *, department_id, start, end, budget, source_key, currency="USD"):
    """Scope payments AND caller-supplied budget to the same inclusive date range.

    Budget is an explicit fixture object with its own scope; mismatches fail.
    source_key selects one export population, preventing Week 1 fixture overlap.
    """
    expected = {
        "department_id": str(department_id),
        "start": str(start),
        "end": str(end),
        "currency": currency,
        "source_key": source_key,
    }
    if any(str(budget.get(k)) != str(v) for k, v in expected.items()):
        raise ValueError("Budget and payment scope must match")
    denominator = Decimal(budget["amount"])
    if not denominator.is_finite() or denominator <= 0:
        raise ValueError("Budget must be positive and finite")
    rows = conn.execute(
        """SELECT classification,sum(amount) AS amount FROM payments
      WHERE department_id=%s AND paid_on BETWEEN %s AND %s AND currency=%s
      AND EXISTS (SELECT 1 FROM payment_revisions r JOIN source_imports s USING(import_id)
        WHERE r.payment_id=payments.payment_id AND s.source_key=%s) GROUP BY classification""",
        (department_id, start, end, currency, source_key),
    ).fetchall()
    totals = {
        name: Decimal("0.00") for name in ("consulting", "operational", "unresolved")
    }
    totals.update({row["classification"]: row["amount"] for row in rows})
    return {
        **expected,
        **{k: str(v) for k, v in totals.items()},
        "budget": str(denominator),
        "consulting_share_percent": str(
            (totals["consulting"] / denominator * 100).quantize(Decimal(".01"))
        ),
    }
