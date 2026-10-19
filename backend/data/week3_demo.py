# this file demonstrates the week 3 evidence chain with fictional data
# it checks the totals and old citations in a fresh database, then saves what actually happened
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from backend.engine.models import Report
from .db import ROOT, migrate
from .seed import seed
from .testing import empty_test_database
from .models import AccessContext
from .week2_models import AssignmentInput, DocumentInput
from .week3_models import FactInput, ComparableInput
from .workspace import get_job, save_assignment, DataError
from .ingestion import submit_pdf, process_job
from .history import add_fact, link_document, comparable_work
from .reports import save_report, get_report

DEPT = UUID("10000000-0000-4000-8000-000000000001")
ENG = UUID("30000000-0000-4000-8000-000000000001")
CTX = AccessContext(
    actor_id=UUID("50000000-0000-4000-8000-000000000001"),
    allowed_department_ids=(DEPT,),
)


def run():
    pdf = (ROOT / "tests/fixtures/week2/engagement.pdf").read_bytes()
    metadata = json.loads((ROOT / "tests/fixtures/week2/manifest.json").read_text())[
        "pdf"
    ]
    checks = []

    def check(name, expected, actual):
        checks.append(
            dict(
                check=name, expected=expected, actual=actual, passed=expected == actual
            )
        )
        if expected != actual:
            raise ValueError(f"Check failed: {name}")

    with empty_test_database() as conn:
        migrate(conn)
        seed(conn)
        conn.commit()

        def upload(content, **changes):
            job = submit_pdf(
                conn, content, DocumentInput(**{**metadata, **changes}), CTX
            )
            conn.commit()
            process_job(conn, job)
            conn.commit()
            return get_job(conn, job, CTX)

        first = upload(pdf)
        second = upload(pdf, title="Second fictional document")
        chunk = conn.execute(
            "SELECT * FROM chunks WHERE document_version_id=%s ORDER BY ordinal",
            (first["document_version_id"],),
        ).fetchone()
        for specialty in ["permit processing", "process improvement"]:
            add_fact(
                conn,
                FactInput(
                    engagement_id=ENG,
                    kind="specialty",
                    value=specialty,
                    evidence_chunk_id=chunk["chunk_id"],
                ),
                CTX,
            )
        add_fact(
            conn,
            FactInput(
                engagement_id=ENG,
                kind="outcome",
                unknown_reason="The fixture has no measured outcome",
                evidence_chunk_id=chunk["chunk_id"],
            ),
            CTX,
        )
        link_document(conn, ENG, second["document_version_id"], CTX)
        case = comparable_work(conn, ComparableInput(specialty="permit"), CTX)[0]
        check("two documents", 2, len(case["documents"]))
        check(
            "two specialties",
            2,
            len([f for f in case["facts"] if f["kind"] == "specialty"]),
        )
        check(
            "week 1 payment total stays unchanged",
            "300.00",
            str(case["payments"][0]["amount"]),
        )
        saved = save_assignment(
            conn,
            AssignmentInput(
                problem="Improve permit intake",
                department_id=DEPT,
                intended_result="Preliminary plan",
                selected_document_version_ids=[first["document_version_id"]],
            ),
            CTX,
        )
        report = Report(
            report_id=str(uuid4()),
            assignment_id=str(saved["assignment_id"]),
            sections=[
                dict(
                    name="findings",
                    content="The fictional timeline is six weeks.",
                    citation_ids=["c1"],
                )
            ],
            citations=[
                dict(citation_id="c1", evidence_chunk_id=str(chunk["chunk_id"]))
            ],
        )
        save_report(conn, report, CTX)
        newer = upload(pdf + b"\n", document_id=first["document_id"])
        check(
            "changed bytes create a new version",
            True,
            newer["document_version_id"] != first["document_version_id"],
        )
        restored = get_report(conn, report.report_id, 1, CTX)
        check(
            "old citation still resolves version 1",
            str(first["document_version_id"]),
            str(restored["citations"][0]["source"]["document_version_id"]),
        )
        check(
            "old citation text stays unchanged",
            chunk["text"],
            restored["citations"][0]["source"]["text"],
        )
        report.report_id = str(uuid4())
        report.citations[0].evidence_chunk_id = str(uuid4())
        try:
            save_report(conn, report, CTX)
        except DataError as exc:
            check(
                "missing citation rejected", "source_not_ready_or_not_allowed", exc.code
            )
        else:
            check("missing citation rejected", True, False)
        check(
            "failed save leaves no extra report",
            1,
            conn.execute("SELECT count(*) AS n FROM reports").fetchone()["n"],
        )
        return dict(
            synthetic=True,
            checks=checks,
            passed=all(c["passed"] for c in checks),
            comparable=case,
            source_versions=dict(
                original=first["document_version_id"],
                newer=newer["document_version_id"],
            ),
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run the fictional week 3 evidence demo"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "evidence/local/week3-demo.json"
    )
    args = parser.parse_args()
    record = run()
    paths = sorted((ROOT / "backend").rglob("*.py")) + sorted(
        (ROOT / "backend/data/migrations").glob("*.sql")
    )
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(ROOT)).encode() + b"\0" + path.read_bytes())
    record.update(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_sha256=digest.hexdigest(),
        code_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, default=str, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": record["passed"],
                "checks": len(record["checks"]),
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
