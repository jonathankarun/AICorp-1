# Fetched branch additions

[Handbook home](README.md) · [Exact branch symbols and fields](branch-symbols.md)

These branches were fetched from GitHub on October 6, 2026. They were inspected
without merging them into `main`. Links below pin the inspected commits so later
branch movement will not silently change this snapshot. The main handbook
remains a description of `main` at `450122f`.

## Jai's Week 2/3 engine — jai-week2-3 at 2fdb258

[Browse source](https://github.com/jonathankarun/AICorp-1/tree/2fdb258)

Adds `backend/engine/demo_*.py` alongside the original engine, a v2 prompt,
retrieval evaluation, Week 2/3 CLI demos, tests, fixtures, and recorded evidence.
It does not replace the main workspace API or add a live provider.

### Inputs and outputs

The demo Assignment adds optional `topic`. EvidenceChunk adds optional
`content_hash` and `department_id`. The demo AccessContext uses string actor ID,
readable scope names (default fixture/public), and an external-use flag; it is
distinct from the database UUID/department AccessContext.

The result union adds `evidence_gap` with assignment ID, message, query,
rejected chunk IDs, and model-call count. A successful result adds
`retrieval_trace`, `evidence_map`, and `methodology_stages`. Report adds nullable
`cost_evidence` and `run_id`; UsageRecord adds `elapsed_ms`. Exact field/default
lists are in the branch symbol inventory.

### Retrieval and consulting process

1. Validate assignment and check scope before model use.
2. `prepare_query()` combines problem, intended result, topic, and requested sections.
3. `FixtureEvidenceRepository.search_evidence()` filters selected versions/department, scores keyword/title overlap, drops weak incidental matches, and sorts deterministically.
4. `_select_context()` checks readable scopes and external-use permission, deduplicates hash/normalized text, and chooses bounded evidence. Defaults are five chunks and a 450-word context.
5. No evidence produces `evidence_gap` before generation.
6. `build_evidence_map()` maps requested sections to chunks using section-specific token hints; unknown section names use up to the first two chunks. Missing support is flagged explicitly. This is a heuristic map, not semantic verification.
7. `calculate_cost_evidence()` gets comparison records and computes Decimal minimum/maximum. Missing records produce null amounts and a reason. Fixture records are fictional $12,000–$15,000 payments, not a new quote or the workspace spending totals.
8. `build_generation_context()` supplies the evidence map, cost evidence, and eight stages: clarify, identify stakeholders/constraints, retrieve, compare prior work, identify gaps, develop alternatives, assess tradeoffs, recommend next steps.
9. The saved-response adapter records evidence/context and returns mock report/usage. Validation checks citations and required sections, then overwrites cost evidence with the deterministic calculation.

The Jai branch's context guard allows an oversized first chunk through; the
integrated branch below fixes that condition. Do not assume the two commits have
identical retrieval behavior. Historical-cost arithmetic is designed around the
homogeneous fixture corpus; it does not normalize mixed currencies or establish
real-world comparability of arbitrary records.

### Commands and evaluation

Run only in a checkout containing this branch:

```bash
.venv/bin/python scripts/demo_jai_week2.py
.venv/bin/python scripts/demo_jai_week3.py
.venv/bin/python -m evaluation.retrieval_baseline
.venv/bin/python -m pytest tests/test_engine_week2.py tests/test_engine_week3.py -q
```

Evaluation input defaults to `evaluation/retrieval_queries.json`; CLI accepts
`--queries` and `--output`. Output includes answerable top-five hits, all behavior
checks, and per-query selected/rejected IDs. The committed demo documentation
reports 9/9 answerable and 12/12 overall behavior checks, not a general accuracy
claim. Demo scripts write contributor evidence files; these results were not
rerun merely by fetching the branch.

## Yasha's original frontend — yasha-week1 at 2176e8a

[Browse source](https://github.com/jonathankarun/AICorp-1/tree/2176e8a)

Adds a standalone React form/report viewer and an independent in-memory FastAPI
API in `backend/api/main.py`. The commit title says Week 7, while source and
project documentation describe the Week 1 workflow. This page follows the code.

### Historical API contract

- `GET /api/v1/health`: returns status/service/week; no authentication.
- `POST /api/v1/assignments`: accepts AssignmentCreate and returns HTTP 201 AssignmentResponse. Requires nonblank problem, department, intended result, audience, and at least one normalized requested section. Uses text fixture IDs, not the shared database UUID contract.
- `GET /api/v1/assignments/{assignment_id}`: returns the in-memory record or HTTP 404 with `detail: "assignment not found"`.
- Validation errors are HTTP 422 with code `VALIDATION_ERROR`, message, and `{field, message}` entries.
- AssignmentResponse adds server UUID string, schema `1.0`, and `created_by: "local-demo-user"`. Records disappear on restart.

CORS permits the two local Vite origins on port 5173. `VITE_API_BASE_URL` defaults
to `http://localhost:8000`. The UI's `createAssignment()` posts the form;
`checkHealth()` reports server health; `ApiValidationError` carries field errors.
`AssignmentForm` normalizes/sends values and displays field errors. `ReportView`
formats section names, resolves citation IDs, and opens source details. Its report
is a hardcoded fixture independent of the newly saved assignment.

This API is historical and unauthenticated. Its schema, startup command, and
error format should not be used as the current main-branch contract.

## Integrated workspace — yasha-week2 at 7d6562a

[Browse source](https://github.com/jonathankarun/AICorp-1/tree/7d6562a)

Combines Jonathan's current database/workspace, Jai's demos, and Yasha's form and
report viewer. Keeps the authenticated shared API and removes the independent
in-memory API from the active path. `backend.api.main:app` becomes an alias of
`backend.api.app:app`.

### Additional HTTP endpoint

`POST /api/v1/assignments/{identifier}/consult` requires the same bearer token as
the shared API and a saved assignment UUID. No request body is defined; it loads
the persisted assignment instead of accepting a replacement from the caller.

1. Check ownership and allowed department through `get_assignment()`.
2. Parse a demo Assignment; reject an empty required-section list with HTTP 422 `required_sections_missing`.
3. Build WorkspaceEvidenceRepository, WorkspaceMockAdapter, and server-derived engine access context.
4. Run the demo pipeline and return its result dictionary plus `evidence`.

HTTP 200 may contain `report`, `needs_input`, `evidence_gap`, or engine `error`;
clients must inspect `result_type`. Infrastructure/access/request failures use
the shared API's HTTP error responses. `evidence` is the adapter's retrieved
chunk list; before-model early returns leave it empty.

### New bridge and interface behavior

- `WorkspaceEvidenceRepository.search_evidence()`: uses PostgreSQL search with the saved assignment's department, selected versions, and external-use eligibility; converts rows to demo EvidenceChunk models. It never falls back to fixture evidence.
- `get_historical_costs()`: returns an empty list because a comparable population/date/source scope has not been defined. The report therefore has null cost amounts and an explanation.
- `WorkspaceMockAdapter.generate()`: quotes supporting source text into required sections, uses actual chunk IDs for citations, labels the result mock, and returns mock usage. It does not create live consulting recommendations.
- `apiRequest()` centralizes authenticated HTTP calls and error-field display.
- `App` retains upload/save/search/restore, adds dirty/report state and `consult()`, and clears prior reports on edits/reconnect/save.
- `AssignmentForm` takes form/documents/busy/onChange/onSubmit props, supports problem/RFP/RFQ, and disables controls during requests.
- `ReportView` takes the actual returned report/evidence, displays source text, page locator, chunk ID, and version ID when a citation is clicked. `labelFromName()` turns underscore section names into readable headings.
- The retrieval budget guard now skips any whole chunk exceeding the remaining word budget, including the first chunk.
- Launcher/browser configuration supports `AICORP_PORT`; Vitest report-viewer checks are added to CI alongside Playwright.

Reports remain transient; no database report/version storage is added. Mock
fixtures remain for regression tests. Production identity, live providers,
semantic retrieval, and a real scoped comparison-cost adapter remain future work.

The branch's committed integration notes report 55 backend tests, two browser
tests, a frontend build, and a viewer unit test passing. Those are historical
reported results, not a new verification performed for this handbook.
