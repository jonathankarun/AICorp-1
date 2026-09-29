"""Local connection configuration and transactional, checksummed migrations."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = Path(__file__).parent / "migrations"


def connect(database: str | None = None, *, autocommit: bool = False):
    """Environment values override the ignored local .env; never print secrets."""
    load_dotenv(ROOT / ".env", override=False)
    password = os.environ.get("POSTGRES_PASSWORD", "")
    if not password or password == "replace-with-a-local-password":
        raise ValueError("Set POSTGRES_PASSWORD in .env or run scripts/setup_local.py")
    return psycopg.connect(
        host=os.environ.get("PGHOST", "127.0.0.1"),
        port=int(os.environ.get("POSTGRES_PORT", "55432")),
        user=os.environ.get("POSTGRES_USER", "aicorp"),
        password=password,
        dbname=database or os.environ.get("POSTGRES_DB", "aicorp"),
        connect_timeout=10,
        autocommit=autocommit,
        row_factory=dict_row,
    )


def migrate(conn) -> list[str]:
    """Apply new SQL files once; reject edits to already applied migrations."""
    applied = []
    with conn.transaction():
        # Serialize competing startup processes until this transaction commits.
        conn.execute("SELECT pg_advisory_xact_lock(2026092701)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for path in sorted(MIGRATIONS.glob("*.sql")):
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            previous = conn.execute(
                "SELECT sha256 FROM schema_migrations WHERE version = %s", (path.name,)
            ).fetchone()
            if previous:
                if previous["sha256"] != digest:
                    raise ValueError(f"Applied migration changed: {path.name}; add a new migration")
                continue
            conn.execute(content.decode("utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations (version, sha256) VALUES (%s, %s)",
                (path.name, digest),
            )
            applied.append(path.name)
    return applied

