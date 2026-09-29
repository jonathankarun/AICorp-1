from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import MockModelAdapter
from .pipeline import run_engine


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jai's Week 1 mock consulting engine")
    parser.add_argument("assignment", help="Path to Assignment JSON")
    parser.add_argument("--output", default="engine_result.json", help="Where to write result JSON")
    parser.add_argument(
        "--mock-response",
        default="tests/fixtures/mock_report.json",
        help="Saved model response fixture",
    )
    args = parser.parse_args()

    assignment = json.loads(Path(args.assignment).read_text())
    adapter = MockModelAdapter(args.mock_response)
    result = run_engine(assignment, adapter)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2))
    print(result.model_dump_json(indent=2))
    print(f"\nWrote: {output_path}")
    return 0 if result.result_type != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
