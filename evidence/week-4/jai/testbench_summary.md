# Jai Week 4 Testbench Results

- Total cases: **12**
- Passed: **12**
- Failed: **0**
- Pass rate: **100.0%**
- False successes: **0**
- Retry policy respected: **True**
- Max provider attempts observed: **2**

| Case | Scenario | Expected | Actual | Attempts | Result |
|---|---|---|---|---:|---|
| W4-01 | Ordinary supported report regression | report | report | 1 | PASS |
| W4-02 | Missing evidence stops before generation | evidence_gap | evidence_gap | 0 | PASS |
| W4-03 | Missing scope returns specific clarification | needs_input | needs_input | 0 | PASS |
| W4-04 | Fake citation is rejected | invalid_citation | invalid_citation | 1 | PASS |
| W4-05 | Unsupported numeric claim is rejected | unsupported_numeric_claim | unsupported_numeric_claim | 1 | PASS |
| W4-06 | Malformed model JSON fails immediately | malformed_model_output | malformed_model_output | 1 | PASS |
| W4-07 | Provider timeout uses capped retries | provider_timeout | provider_timeout | 2 | PASS |
| W4-08 | Whole-run timeout returns controlled failure | run_timeout | run_timeout | 1 | PASS |
| W4-09 | Prompt-injection text is treated as untrusted evidence | report | report | 1 | PASS |
| W4-10 | Conflicting source amounts remain visibly unresolved | report | report | 1 | PASS |
| W4-11 | Revision preserves trace and reassesses changed requirement | report | report | 1 | PASS |
| W4-12 | Oversized provider output is rejected | output_too_large | output_too_large | 1 | PASS |
