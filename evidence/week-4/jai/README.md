# Jai Week 4 Evidence Package

## Outcome

The Week 4 hardened consulting-engine testbench handles adversarial evidence and provider failures without false success, uncontrolled retries, or hidden uncertainty.

## Exact commands

```powershell
python -m pytest tests/test_engine_week4.py -q
python scripts/demo_jai_week4.py
```

## Actual validation result

- Automated tests: **12 passed**
- Testbench cases: **12/12 passed**
- Pass rate: **100.0%**
- False-success count: **0**
- Retry policy respected: **True**
- Maximum provider attempts observed: **2**

Category results:

- Citation integrity: 2/2
- Conflict handling: 1/1
- Insufficient information: 2/2
- Prompt injection: 1/1
- Provider failures: 4/4
- Regression success: 1/1
- Revision behavior: 1/1

## Representative input/output evidence

- **Prompt injection:** source contains “ignore prior instructions” and an admin-role instruction. The engine flags it, treats it as untrusted evidence, and records no permission change or external action.
- **Fake citation:** mock output points to a nonexistent chunk. The engine returns `invalid_citation` and no report.
- **Provider timeout:** mock provider times out. The engine stops after 2 attempts and returns a retryable `provider_timeout` with no completed report.
- **Conflicting amounts:** two source-backed values (12000.00 and 18000.00) remain visible as an unresolved conflict and trigger expert review.
- **Missing evidence:** engine returns `evidence_gap` before any provider call.
- **Missing scope:** engine returns `needs_input` with the missing field before any provider call.

## Files

- `expected_outputs.md` — expected behavior written before running the testbench.
- `testbench_results.json` — complete input/expected/actual/pass-fail record.
- `testbench_summary.md` — compact metrics and case table.

## Limitation

These results use synthetic fixtures and a deterministic mock provider. They validate code behavior and failure handling; they do not establish real consulting accuracy, production security, or City approval.
