"""Disposable databases shared by the Week 1 validator and integration tests."""
from contextlib import contextmanager
from uuid import uuid4

from psycopg import sql

from .db import connect


@contextmanager
def empty_test_database():
    """Create a fresh random database, never reset a supplied database name.

    This requires CREATEDB on the local development role. Cleanup only drops the
    database successfully created by this invocation, including on test failure.
    """
    name = "aicorp_w1_test_" + uuid4().hex
    with connect("postgres", autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            with connect(name) as conn:
                yield conn
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))

