from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.engine.demo_models import AccessContext
from backend.engine.demo_repository import FixtureEvidenceRepository
from backend.engine.demo_retrieval import retrieve_query


def run_baseline(query_file: str | Path = "evaluation/retrieval_queries.json") -> dict:
    cases = json.loads(Path(query_file).read_text())
    repo = FixtureEvidenceRepository()
    ctx = AccessContext()
    results = []
    answerable_passed = 0
    answerable_total = 0
    behavior_passed = 0

    for case in cases:
        bundle = retrieve_query(
            case["query"],
            repo,
            ctx,
            selected_document_version_ids=case.get("selected_document_version_ids"),
            department_id=case.get("department_id", "dept-fixture-001"),
        )
        selected_docs = [item.document_version_id for item in bundle.evidence]
        selected_ids = [item.chunk_id for item in bundle.evidence]
        expected = case.get("expected_document_version_ids", [])
        behavior = case["expected_behavior"]

        if behavior == "answerable":
            answerable_total += 1
            passed = bool(set(expected) & set(selected_docs))
            answerable_passed += int(passed)
        elif behavior == "no_evidence":
            passed = len(selected_ids) == 0
        elif behavior == "forbidden":
            forbidden_ids = set(case.get("forbidden_chunk_ids", []))
            passed = forbidden_ids.isdisjoint(selected_ids)
        else:
            raise ValueError(f"Unknown expected_behavior: {behavior}")

        behavior_passed += int(passed)
        results.append({
            "id": case["id"],
            "query": case["query"],
            "expected_behavior": behavior,
            "selected_chunk_ids": selected_ids,
            "selected_document_version_ids": selected_docs,
            "rejected_chunk_ids": bundle.trace.rejected_chunk_ids,
            "passed": passed,
        })

    return {
        "answerable_top5": {
            "passed": answerable_passed,
            "total": answerable_total,
            "fraction": answerable_passed / answerable_total if answerable_total else 0.0,
        },
        "all_behavior_checks": {
            "passed": behavior_passed,
            "total": len(cases),
            "fraction": behavior_passed / len(cases) if cases else 0.0,
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jai's Week 2 retrieval baseline")
    parser.add_argument("--queries", default="evaluation/retrieval_queries.json")
    parser.add_argument("--output", default="evidence/week-2/jai/retrieval_baseline.json")
    args = parser.parse_args()

    result = run_baseline(args.queries)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nWrote: {output}")
    return 0 if result["all_behavior_checks"]["passed"] == result["all_behavior_checks"]["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
