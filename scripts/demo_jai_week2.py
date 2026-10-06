import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json

from backend.engine.demo_adapters import MockModelAdapter
from backend.engine.demo_pipeline import run_engine
from evaluation.retrieval_baseline import run_baseline

FIX = Path("tests/fixtures")
OUT = Path("evidence/week-2/jai")
OUT.mkdir(parents=True, exist_ok=True)


def load(name):
    return json.loads((FIX / name).read_text())


baseline = run_baseline()
(OUT / "retrieval_baseline.json").write_text(json.dumps(baseline, indent=2))
print("WEEK 2: 12-QUERY RETRIEVAL BASELINE")
print(json.dumps(baseline["answerable_top5"], indent=2))
print(json.dumps(baseline["all_behavior_checks"], indent=2))

no_evidence_adapter = MockModelAdapter(FIX / "mock_report.json")
no_evidence = run_engine(load("assignment_no_evidence.json"), no_evidence_adapter)
(OUT / "no_evidence_result.json").write_text(no_evidence.model_dump_json(indent=2))
print("\nNO-EVIDENCE CASE")
print(no_evidence.model_dump_json(indent=2))

forbidden_adapter = MockModelAdapter(FIX / "mock_report.json")
forbidden = run_engine(load("assignment_forbidden.json"), forbidden_adapter)
(OUT / "forbidden_result.json").write_text(forbidden.model_dump_json(indent=2))
print("\nFORBIDDEN-SOURCE CASE")
print(forbidden.model_dump_json(indent=2))
print(f"Model calls: {forbidden_adapter.call_count}")
