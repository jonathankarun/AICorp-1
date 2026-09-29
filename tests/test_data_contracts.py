import json

from backend.data.db import ROOT
from backend.data.export_contracts import contract_files


def test_published_contracts_match_models_and_fixture():
    for name, expected in contract_files().items():
        actual = json.loads((ROOT / "contracts/data/v1" / name).read_text())
        assert actual == expected, f"Regenerate stale contract: {name}"
