# Jai Week 5 Evidence

Run:

```powershell
python -m pytest tests/test_engine_week5.py -q
python scripts/demo_jai_week5.py
```

The Week 5 testbench demonstrates a fair candidate comparison, quality scoring, cost/latency accounting, a pre-call budget block, measured context tuning, configuration freeze, and Week 4 regression safety.

Generated evidence:

- `testbench_results.json` — machine-readable PASS/FAIL results for all Week 5 accomplishments.
- `testbench_summary.txt` — screenshot-friendly summary.
- `frozen_configuration.json` — selected Week 6 baseline configuration.

Limitation: the candidate outputs, usage, latency, and rates are controlled fixtures rather than live-provider measurements.
