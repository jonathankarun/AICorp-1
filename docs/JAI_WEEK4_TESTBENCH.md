# Jai Week 4 — Validation Metrics and Testbench Guide

## Goal

Week 4 hardens the LLM Consulting Engine against unreliable evidence and provider failures. The testbench uses only synthetic fixtures and deterministic mock provider behavior. It is designed to produce terminal output that can be screenshotted for the TA while still saving machine-readable evidence.

## Validation metrics

The testbench reports:

- **Pass rate** — passed cases / total declared cases.
- **False-success count** — cases that were expected to stop or fail but incorrectly returned a completed report. Target: **0**.
- **Prompt-injection resistance** — hostile source instructions are detected and treated as untrusted evidence; they do not change permissions or authorize actions.
- **Citation integrity** — fake citations are rejected, and exact numeric claims must appear in their cited evidence.
- **Conflict surfacing** — conflicting source-backed values remain visible and require review instead of silently choosing one.
- **Provider failure control** — malformed JSON fails immediately, timeouts are bounded by the configured attempt cap, and oversized output is rejected.
- **Insufficient-information behavior** — missing scope returns `needs_input`; missing eligible evidence returns `evidence_gap`; both stop before a provider call.
- **Revision traceability** — a revision preserves the prior evidence trace and records changed requirements for reassessment.

## Test cases

| ID | Test | Expected behavior |
|---|---|---|
| W4-01 | Ordinary supported report | Valid draft report, one provider call |
| W4-02 | Missing evidence | `evidence_gap`, zero provider calls |
| W4-03 | Missing scope | `needs_input`, specific missing field, zero provider calls |
| W4-04 | Fake citation | `invalid_citation`, no completed report |
| W4-05 | Unsupported numeric claim | `unsupported_numeric_claim` |
| W4-06 | Malformed provider JSON | `malformed_model_output`, no retry |
| W4-07 | Provider timeout | `provider_timeout`, bounded to two attempts, retryable |
| W4-08 | Whole-run timeout | `run_timeout`, controlled failure |
| W4-09 | Prompt injection in evidence | Report can continue, hostile instruction is flagged/ignored, no permission change |
| W4-10 | Conflicting amounts | Both values remain visible and expert review is required |
| W4-11 | Revision | Prior evidence trace is preserved and changed requirements are reassessed |
| W4-12 | Oversized provider output | `output_too_large`, no completed report |

## Basic test commands

Run only Week 4 automated tests:

```powershell
python -m pytest tests/test_engine_week4.py -q
```

Expected terminal result when everything passes:

```text
12 passed
```

Run the screenshot-friendly testbench:

```powershell
python scripts/demo_jai_week4.py
```

The testbench prints a table with the expected result, actual result, provider attempts, and PASS/FAIL for all 12 cases. It then prints the validation metrics and compact examples for prompt injection, conflicting evidence, timeout, and fake citation handling.

## Screenshot explanations

Useful screenshots to capture later:

1. **`12 passed` pytest result** — proves all declared Week 4 automated cases passed.
2. **Testbench case table** — shows example inputs were exercised against expected outputs and records PASS/FAIL.
3. **Validation metrics block** — shows total/pass rate, zero false successes, retry cap compliance, and category scores.
4. **Prompt-injection output (W4-09)** — shows source instructions were detected and ignored as commands; no permission change or external action was authorized.
5. **Conflict output (W4-10)** — shows both source-backed amounts rather than silently choosing one, plus an expert-review indicator.
6. **Timeout output (W4-07)** — shows a retryable typed failure after the bounded number of attempts and no misleading report.
7. **Fake-citation output (W4-04)** — shows a citation to a nonexistent chunk is rejected.

## Data fed through the engine

`evaluation/week4_test_cases.json` contains all 12 synthetic input cases. Each case includes:

- Assignment input
- Evidence chunks
- Mock provider behavior/response
- Timeout/retry/output-size policy
- Expected result

This makes the testbench repeatable and lets another teammate change an input and predict how the output should change.

## Files produced as evidence

Running the testbench writes:

- `evidence/week-4/jai/testbench_results.json` — full inputs/expected/actual/pass-fail results
- `evidence/week-4/jai/testbench_summary.md` — compact score table

## Week 4 requirement coverage

- Failure fixtures: covered by W4-02 through W4-12.
- Source text treated as untrusted: W4-09 and safety prompt v3.
- Citation support: W4-04 and W4-05.
- Conflicting/missing information: W4-02, W4-03, W4-10.
- Timeouts/retries/output bounds: W4-06, W4-07, W4-08, W4-12.
- Revision/regression: W4-01 and W4-11.

Limitation: the Week 4 testbench uses deterministic synthetic data and a mock provider. It validates engine behavior and failure handling, not real-world consulting accuracy or City security approval.
