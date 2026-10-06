import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json

from backend.engine.demo_adapters import MockModelAdapter
from backend.engine.demo_pipeline import run_engine
from backend.engine.demo_repository import FixtureEvidenceRepository, NoCostFixtureRepository

FIX = Path("tests/fixtures")
OUT = Path("evidence/week-3/jai")
OUT.mkdir(parents=True, exist_ok=True)
assignment = json.loads((FIX / "assignment_week3_complete.json").read_text())

print("WEEK 3: COMPLETE SOURCE-BACKED REPORT")
adapter = MockModelAdapter(FIX / "mock_report_week3.json", prompt_version="v2")
result = run_engine(assignment, adapter, repository=FixtureEvidenceRepository())
(OUT / "complete_report_result.json").write_text(result.model_dump_json(indent=2))
print(result.model_dump_json(indent=2))

print("\nWEEK 3: COST-EVIDENCE GAP")
no_cost_adapter = MockModelAdapter(FIX / "mock_report_week3_no_cost.json", prompt_version="v2")
no_cost = run_engine(assignment, no_cost_adapter, repository=NoCostFixtureRepository())
(OUT / "no_cost_result.json").write_text(no_cost.model_dump_json(indent=2))
print(no_cost.model_dump_json(indent=2))

print("\nWEEK 3: FAKE CITATION REJECTION")
bad_adapter = MockModelAdapter(FIX / "mock_report_week3_bad_citation.json", prompt_version="v2")
bad = run_engine(assignment, bad_adapter, repository=FixtureEvidenceRepository())
(OUT / "bad_citation_result.json").write_text(bad.model_dump_json(indent=2))
print(bad.model_dump_json(indent=2))
