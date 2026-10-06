# Jai — Weeks 2 and 3 Demo

## Week 2: retrieval baseline

Run:

```powershell
python -m pytest tests/test_engine_week2.py -q
python scripts/demo_jai_week2.py
```

What it demonstrates:
- 12 labeled retrieval queries are evaluated before tuning.
- Answerable queries check whether the expected document is in the top five.
- Unrelated requests return an explicit evidence gap instead of fabricating support.
- A selected but forbidden source is rejected before the model call.
- The captured model input never contains the forbidden chunk.
- Context is deduplicated, source-aware, and limited by configurable chunk/word caps.

Expected test result: `4 passed`. The baseline should report `9/9` answerable top-five checks and `12/12` overall behavior checks.

## Week 3: complete source-backed report

Run:

```powershell
python -m pytest tests/test_engine_week3.py -q
python scripts/demo_jai_week3.py
```

What it demonstrates:
- The engine exposes the consulting sequence: clarify, stakeholders/constraints, retrieve, compare prior work, identify gaps, alternatives, tradeoffs, and next steps.
- It creates an evidence map for each requested report section before generation.
- Historical cost range is calculated in deterministic Python code from fictional actual-payment records (`12000.00`–`15000.00` USD), not trusted to model arithmetic.
- Missing cost evidence produces null amounts plus a reason.
- Fake citation IDs are rejected as `invalid_model_output`.
- The final report contains all requested sections and citations that resolve to retrieved chunks.

Expected test result: `4 passed`.

## All Jai engine tests

```powershell
python -m pytest tests/test_engine.py tests/test_engine_week2.py tests/test_engine_week3.py -q
```

Expected result: `11 passed`.

All fixtures are synthetic. Live provider comparison remains pending until model/provider/data-use authorization and allowance are confirmed.
