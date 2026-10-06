# Week 2 — Jai

Purpose: demonstrate measurable retrieval behavior using synthetic evidence.

Commands:
- `python -m pytest tests/test_engine_week2.py -q`
- `python scripts/demo_jai_week2.py`

Expected: 4 tests pass; 9/9 answerable queries find a relevant document in the top five; all 12 labeled behavior checks pass; unrelated evidence returns an evidence gap; forbidden evidence never enters the mock model request.

Limitation: this is a controlled keyword baseline over synthetic fixtures. Live model comparison is intentionally not claimed.
