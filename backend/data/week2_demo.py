"""Reproducible Week 2 import, persistence and retrieval baseline in a fresh DB."""

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from .db import ROOT, migrate
from .seed import seed
from .testing import empty_test_database
from .models import AccessContext
from .week2_models import AssignmentInput, DocumentInput, SearchInput
from .workspace import get_job, save_assignment, get_assignment
from .ingestion import submit_pdf, process_job
from .importer import import_csv, spending
from .search import search

FIX = ROOT / "tests/fixtures/week2"
DEPT = UUID("10000000-0000-4000-8000-000000000001")
CTX = AccessContext(
    actor_id=UUID("50000000-0000-4000-8000-000000000001"),
    allowed_department_ids=(DEPT,),
)


def run():
    manifest = json.loads((FIX / "manifest.json").read_text())
    budget = json.loads((FIX / "budget.json").read_text())
    with empty_test_database() as conn:
        migrate(conn)
        seed(conn)
        conn.commit()
        first = import_csv(conn, (FIX / "payments.csv").read_bytes(), manifest)
        repeat = import_csv(conn, (FIX / "payments.csv").read_bytes(), manifest)
        totals = spending(
            conn,
            department_id=DEPT,
            start=budget["start"],
            end=budget["end"],
            budget=budget,
            source_key=manifest["source_key"],
        )
        assert (
            totals["consulting"] == "280.00"
            and totals["consulting_share_percent"] == "2.80"
        )
        assert (
            totals["unresolved"] == "50.00"
            and repeat["unchanged"] == 5
            and repeat["inserted"] == 0
        )
        bad = import_csv(
            conn,
            (FIX / "payments.csv").read_bytes().replace(b"100.00", b"not-money"),
            manifest,
        )
        assert len(bad["rejected"]) == 1
        conn.execute(
            "INSERT INTO departments VALUES(%s,'other-week2','Other fictional department','fixture://other')",
            (UUID("10000000-0000-4000-8000-000000000002"),),
        )
        conn.commit()
        versions = {}
        for label in ("approved", "external_disallowed", "other_department"):
            meta = DocumentInput(**manifest["pdf"])
            context = CTX
            if label == "external_disallowed":
                meta = meta.model_copy(update={"external_model_allowed": False})
            if label == "other_department":
                other = UUID("10000000-0000-4000-8000-000000000002")
                meta = meta.model_copy(update={"department_id": other})
                context = AccessContext(
                    actor_id=CTX.actor_id, allowed_department_ids=(other,)
                )
            job_id = submit_pdf(
                conn, (FIX / "engagement.pdf").read_bytes(), meta, context
            )
            conn.commit()
            process_job(conn, job_id)
            conn.commit()
            versions[label] = get_job(conn, job_id, context)["document_version_id"]
        saved = save_assignment(
            conn,
            AssignmentInput(
                problem="Improve permit processing",
                department_id=DEPT,
                intended_result="Preliminary improvement plan",
                selected_document_version_ids=[versions["approved"]],
            ),
            CTX,
        )
        conn.commit()
        restored = get_assignment(conn, saved["assignment_id"], CTX)
        assert restored["selected_document_version_ids"] == [str(versions["approved"])]
        results = []
        for case in json.loads((ROOT / "evaluation/week2_queries.json").read_text()):
            if case["split"] != "development":
                continue
            selected = [versions[case["selected"]]] if "selected" in case else None
            result = search(
                conn,
                SearchInput(
                    query=case["query"], selected_document_version_ids=selected
                ),
                CTX,
            )
            returned = [str(c["document_version_id"]) for c in result["chunks"]]
            expected = str(versions[case["expected"]]) if case["expected"] else None
            passed = expected in returned if expected else not returned
            results.append(
                {
                    **case,
                    "expected_document_id": expected,
                    "returned_document_ids": returned,
                    "returned_chunk_ids": [
                        str(c["chunk_id"]) for c in result["chunks"]
                    ],
                    "passed": passed,
                }
            )
        answerable = [r for r in results if r["expected"]]
        hits = sum(r["passed"] for r in answerable)
        gaps = [r for r in results if not r["expected"]]
        assert all(r["passed"] for r in gaps)
        conn.commit()
        return {
            "first_import": first,
            "repeat_import": repeat,
            "rejected_row_example": bad["rejected"],
            "spending": totals,
            "assignment": restored,
            "corpus_versions": versions,
            "retrieval": results,
            "baseline": {
                "hits_at_5": hits,
                "answerable_development_queries": len(answerable),
                "fraction": hits / len(answerable),
                "no_evidence_and_forbidden_passed": len(gaps),
                "holdout_queries_not_run": 2,
                "limitation": "Keyword search misses turnaround bottlenecks; no semantic tuning performed.",
            },
            "live_model_evaluation": "pending authorization; no paid calls",
            "deterministic_checks_passed": True,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "evidence/local/week2-demo.json"
    )
    args = parser.parse_args()
    record = run()
    record.update(
        generated_at=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        fixture_sha256=hashlib.sha256(
            (FIX / "engagement.pdf").read_bytes()
        ).hexdigest(),
        synthetic=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, default=str, indent=2) + "\n")
    print(
        json.dumps(
            {
                "spending": record["spending"],
                "baseline": record["baseline"],
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
