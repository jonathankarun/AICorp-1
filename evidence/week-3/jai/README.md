# Week 3 — Jai

Purpose: demonstrate a complete structured consulting-engine path with traceable evidence.

Commands:
- `python -m pytest tests/test_engine_week3.py -q`
- `python scripts/demo_jai_week3.py`

Expected: 4 tests pass; the complete fixture returns every requested section; citation IDs resolve to retrieved evidence; deterministic historical actual-payment range is 12000.00–15000.00 USD; missing costs remain null with a reason; a fake citation is rejected.

Limitation: report text is still a saved mock provider response. These checks prove engine structure, retrieval/citation handling, and deterministic calculations—not City-validated consulting quality.
