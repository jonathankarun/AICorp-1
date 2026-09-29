"""Insert the fixed Week 1 fixture atomically, with no duplicate or silent updates."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from uuid import UUID

from psycopg import sql

from .db import ROOT

FIXTURE_PATH = ROOT / "tests/fixtures/data_week1.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def seed(conn) -> dict[str, int]:
    data = load_fixture()
    inserted = {}
    with conn.transaction():
        # A changed fixture must fail visibly, not overwrite an existing record.
        for table, records in (
            ("departments", [data["department"]]),
            ("vendors", [data["vendor"]]),
            ("engagements", [data["engagement"]]),
            ("payments", data["payments"]),
        ):
            inserted[table] = 0
            for record in records:
                values = {
                    key: UUID(value) if key.endswith("_id") and value is not None
                    else Decimal(value) if key == "amount"
                    else date.fromisoformat(value) if key == "paid_on"
                    else value
                    for key, value in record.items()
                }
                cursor = conn.execute(
                    sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (source_key) DO NOTHING").format(
                        sql.Identifier(table),
                        sql.SQL(", ").join(map(sql.Identifier, values)),
                        sql.SQL(", ").join(sql.Placeholder() for _ in values),
                    ),
                    tuple(values.values()),
                )
                inserted[table] += cursor.rowcount
                existing = conn.execute(
                    sql.SQL("SELECT {} FROM {} WHERE source_key = %s").format(
                        sql.SQL(", ").join(map(sql.Identifier, values)), sql.Identifier(table)
                    ),
                    (record["source_key"],),
                ).fetchone()
                if existing != values:
                    raise ValueError(f"Seed conflict in {table}: {record['source_key']}; review existing data")
    return inserted

