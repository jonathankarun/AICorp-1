# Jai Week 5 — Quality, Cost, and Configuration Selection

## Goal

Week 5 chooses settings using measured quality and cost evidence. The development runner holds the assignment, evidence, prompt version, and retrieval version constant across candidates and uses an equal number of runs for each candidate.

## Scoring sheet

Each successful report is scored out of 100:

| Dimension | Weight |
|---|---:|
| Required-section coverage | 20 |
| Factual support | 25 |
| Citation quality | 20 |
| Completeness | 15 |
| Usefulness | 10 |
| Feasibility | 10 |

Usefulness and feasibility are reviewer scores from 1–5. The fixture labels them **peer review**, not City subject-matter review.

Critical unsupported claims are counted separately and can fail the quality gate.

## Controlled comparison

The development fixture defines two provider-neutral candidates:

- `low_cost_candidate`
- `stronger_candidate`

Both receive the same assignment/evidence and three runs each. A failed run remains in the results and receives a zero quality score; failures are not discarded from the comparison.

The included rate schedule and usage values are synthetic fixtures for testing the accounting path. Replace them with dated provider rates and provider-reported usage before making a live-provider selection claim.

## Usage and cost

For each attempt the runner records:

- model ID
- estimated input tokens used by the fixture
- fixture output tokens
- provider-fixture elapsed time
- local engine elapsed time
- retries
- revisions
- rate date
- rate unit
- input/output rate
- actual fixture cost
- reserved maximum cost

The maximum reservation is calculated **before** the provider call using estimated input size plus the configured output cap.

## Budget control

`BudgetLedger` uses a lock and reserves the maximum cost before calling the provider. If the reservation would exceed the remaining allowance, the run returns:

```text
code = budget_exceeded
provider_calls = 0
```

The separate budget demo intentionally uses a tiny allowance to prove this behavior.

## Measured tuning

The development evidence deliberately includes one duplicate passage. The baseline records the duplicate. The tuned run removes only the repeated text, records the removed chunk ID, and measures the change in estimated input tokens.

This is the only tuning made in the fixture because Week 5 says to change only a measured weakness and change one factor at a time.

## Freeze behavior

A candidate passes only when:

- all development runs succeed,
- average score meets the configured minimum,
- every run has complete required-section coverage,
- critical unsupported claims remain within the configured limit.

The runner then chooses the lowest-cost candidate among those that pass. The chosen model/configuration, prompt version, retrieval version, corpus version, quality gate, and deduplication setting are written to `frozen_configuration.json`.

## Regression checks

The demo reruns these Week 4 cases when the Week 4 testbench is present:

- no evidence
- fake citation
- prompt injection
- conflicting evidence

This checks that Week 5 tuning does not break previously passing safety behavior.

## What to screenshot

1. `python -m pytest tests/test_engine_week5.py -q`
2. `python scripts/demo_jai_week5.py`
3. `evidence/week-5/jai/frozen_configuration.json`

The terminal demo is designed to show candidate success count, average quality score, average cost, latency, quality-gate result, the selected configuration, the budget-block result with zero provider calls, and Week 4 regression status.

## Accomplishment testbench

`evaluation/week5_testbench.py` converts the Week 5 work into eight simple acceptance checks:

1. Same assignment/evidence and equal run counts for a fair comparison.
2. Repeatable quality scoring.
3. Quality-gate behavior: weaker fixture fails and stronger fixture passes.
4. Cost and latency accounting.
5. Budget block before a provider call.
6. Measured duplicate-context removal and token savings.
7. Selected configuration frozen for Week 6.
8. Week 4 safety regressions still pass.

Run it through:

```powershell
python scripts/demo_jai_week5.py
```

It writes `testbench_results.json` and `testbench_summary.txt` under `evidence/week-5/jai/`.
