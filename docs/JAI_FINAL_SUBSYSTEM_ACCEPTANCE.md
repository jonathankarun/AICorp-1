# Jai — LLM Consulting Engine Final Acceptance and Demo Guide

## What is complete

This final layer maps Jai's subsystem work to the team's Execution Timeline and Validation Plan and gives the TA one live walkthrough instead of separate weekly scripts.

### Execution Timeline coverage

| Execution activity | Jai subsystem evidence | Final demo checkpoint |
|---|---|---|
| Status Update 1 — LLM engine models + mock generation pipeline | `backend/engine/models.py`, `adapters.py`, `pipeline.py`, `tests/test_engine.py` | VP-1.3 |
| Status Update 2 — Evidence retrieval + labeled-query baseline | engine retrieval contract + final 12-query fixture baseline | VP-2.4 |
| Status Update 3 — Structured evidence-backed report generation | hardened structured report path | VP-3.1, VP-3.2 |
| Status Update 4 — Citation validation + adversarial/failure testing | Week 4 engine/testbench | VP-4.3, VP-4.4 |
| Status Update 5 — LLM quality/model/cost comparison | Week 5 scoring, quality gate, budget ledger | VP-5.4, VP-5.5, VP-5.6 |
| Status Update 6 — LLM consulting engine acceptance/release | frozen configuration + shared Assignment/Report contracts | VP-6.2 |
| Status Update 7 — LLM results/limitations demonstration | one end-to-end success and one controlled failure | VP-7.1, VP-7.2 |
| Longevity bonus | model lifecycle registry and benchmark-gated replacement | EXTRA-L1 |

## Validation Plan coverage

The GUI executes these Validation Plan items directly:

- **VP-1.3 — LLM Engine Scope Validation**
- **VP-2.4 — Retrieval Relevance** (Jai's engine-side portion; shared with Data)
- **VP-3.1 — Structured Report Generation**
- **VP-3.2 — Citation Traceability** (shared with Data)
- **VP-4.3 — Prompt Injection / Unsupported Evidence**
- **VP-4.4 — Model Failure Recovery** (shared with Application)
- **VP-5.4 — LLM Evidence Quality**
- **VP-5.5 — Report Usefulness**
- **VP-5.6 — API Cost Control** (shared with Application)
- **VP-6.2 — Release Compatibility** (Jai's engine-contract portion)
- **VP-7.1 — Full System Demonstration** (Jai's engine portion)
- **VP-7.2 — Controlled System Failure Demo** (Jai's engine portion)

## Run the final automated acceptance

```powershell
python -m pytest tests/test_jai_final_acceptance.py -q
python scripts/run_jai_final_acceptance.py
```

Saved evidence:

```text
evidence/final/jai/acceptance_results.json
evidence/final/jai/acceptance_summary.txt
```

## Run the live browser walkthrough

```powershell
python scripts/serve_jai_final_demo.py
```

Open:

```text
http://127.0.0.1:8010
```

The page is designed for a presentation:

1. Select the next VP checkpoint on the left.
2. Read the **What this check proves** statement.
3. Click **Run this checkpoint**.
4. Show the live input, output, and measurable metrics.
5. Read the plain-language explanation shown with the checkpoint and connect it to the live result.
6. Click **Next checkpoint**.

## Suggested walkthrough flow

### 1 — Scope gate
Explain that the model is never called if the assignment is incomplete. The output should show `needs_input` and zero model calls.

### 2 — Retrieval
Explain that generation quality starts with the correct evidence. Show top-five relevance and that forbidden evidence has zero context leaks.

### 3 — Structured report
Show the requested consulting sections and explain that this is a typed report contract, not free-form chatbot text.

### 4 — Citations
Show valid evidence IDs, then the fake-citation rejection. Explain that a citation must resolve to evidence actually given to the model.

### 5 — Adversarial evidence
Show the source text trying to say `IGNORE PRIOR INSTRUCTIONS`. Explain that document text is untrusted data and cannot change permissions. Also show an unsupported exact number being rejected.

### 6 — Failure recovery
Show a provider timeout reaching the attempt cap and returning a controlled error with `report: null`.

### 7 — Evidence quality
Show factual-support percentage, section coverage, and unsupported-claim count. Explain the repeatable quality rubric.

### 8 — Human usefulness gate
Change one GUI score below 4.0 and rerun to make the checkpoint fail. Restore the score to 4.0+ and rerun to pass. This is the clearest demonstration that human usefulness review is intentionally separate from automated citation checks.

### 9 — Cost control
Point specifically to `provider_calls = 0` for an over-budget request. The budget guard runs before paid provider use.

### 10 — Release compatibility
Show the selected/frozen configuration and shared Assignment/Report identifiers. Explain why interfaces are frozen before final evaluation.

### 11 — End-to-end
Show one result containing retrieval metrics, final report, quality metrics, and cost metrics. This is the complete engine story.

### 12 — Controlled failure
Show a successful report first, then a timeout. The failed run has no new report while the prior report ID remains available.

### Bonus — Model longevity
Show the automatic model lifecycle result and explain that outdated models can be replaced through a registry only after a benchmark passes.


## Final fake assignment -> Yasha application handoff

The revised GUI has a **Run final fake assignment** button in the header. This executes the synthetic assignment through the hardened engine and produces the same shared `Report` contract accepted by `POST /api/v1/reports`.

The page then renders the information the application layer can show to a City user:

- report status and report/version IDs;
- findings;
- alternatives;
- recommendation;
- implementation steps;
- risks;
- citation/source cards with title, locator, and source text;
- assumptions;
- missing information;
- expert-review flags;
- quality/support metrics.

The exact handoff is also written to:

```text
evidence/final/jai/yasha_display_payload.json
```

The JSON contains both `report_contract` (the engine/data API contract) and `application_display` (a presentation-friendly view derived from that contract). This makes the demo useful both visually and as an integration artifact for Yasha's subsystem.

## Important demo boundary

The acceptance GUI intentionally uses controlled synthetic evidence and deterministic provider fixtures. This makes the demonstration reproducible and lets every failure mode be shown on command. It does **not** claim that fixture quality scores are live GPT/Claude measurements or that the local demo is City production security approval.

The real database-backed retrieval adapter remains in `backend/engine/retrieval.py`; the final fixture retrieval baseline represents Jai's engine-side retrieval validation without requiring PostgreSQL during the presentation.

## Technical architecture

```text
Browser GUI (localhost:8010)
          |
          v
FastAPI final_demo_api.py
          |
          v
jai_final_validation.py
    |        |        |
    |        |        +--> Week 5 quality/cost functions
    |        +-----------> Week 4 hardened engine
    +--------------------> Week 1 scope/pipeline contracts
          |
          v
uniform validation result
(input / output / metrics / pass-fail / explanation)
```

The browser, command-line acceptance script, and pytest suite all call the same validation functions. That is deliberate: there is no separate "presentation-only" implementation that could disagree with the tests.
