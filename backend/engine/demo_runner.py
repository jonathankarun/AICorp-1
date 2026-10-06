from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo_adapters import MockModelAdapter
from .demo_pipeline import run_engine
from .demo_repository import FixtureEvidenceRepository, NoCostFixtureRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jai's mock consulting engine (Weeks 1-3)")
    parser.add_argument("assignment", help="Path to Assignment JSON")
    parser.add_argument("--output", default="engine_result.json", help="Where to write result JSON")
    parser.add_argument(
        "--mock-response",
        default="tests/fixtures/mock_report.json",
        help="Saved model response fixture",
    )
    parser.add_argument("--prompt-version", default="v1", help="Prompt/configuration version label")
    parser.add_argument(
        "--no-cost-evidence",
        action="store_true",
        help="Use the Week 3 fixture repository with comparable cost evidence removed",
    )
    args = parser.parse_args()

    assignment = json.loads(Path(args.assignment).read_text())
    adapter = MockModelAdapter(args.mock_response, prompt_version=args.prompt_version)
    repository = NoCostFixtureRepository() if args.no_cost_evidence else FixtureEvidenceRepository()
    result = run_engine(assignment, adapter, repository=repository)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2))
    print(result.model_dump_json(indent=2))
    print(f"\nWrote: {output_path}")
    return 0 if result.result_type != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
