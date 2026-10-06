# Frontend and team integration — October 6, 2026

## What was integrated

The local `yasha-week2` checkout originally matched GitHub `main` at `450122f`.
The only uncommitted change was generated Python bytecode. Yasha's actual
frontend implementation was already committed on `yasha-week1` at `2176e8a`.
After fetching GitHub, this branch fast-forwarded to Jai's `jai-week2-3` at
`2fdb258`, which includes Jonathan's latest main-branch work, then merged
Yasha's branch with the shared-file conflicts resolved.

| Contributor | Existing work retained | Integration change |
| --- | --- | --- |
| Yasha | Assignment fields, report sections, citation/source viewer, viewer test | Form now saves to the authenticated UUID-based API; report viewer receives a validated report and its retrieved evidence from the server |
| Jonathan | PostgreSQL persistence, immutable document versions, upload processing, ready-source selection, authorization, keyword search, financial tests | Added a bridge from his search contract to Jai's repository protocol; kept department, version and external-use checks |
| Jai | Week 1 engine and Week 2/3 retrieval, methodology, evidence-map, cost and citation-validation demos | Shared API invokes his Week 2/3 pipeline with database evidence and a clearly labeled local mock preview adapter |

## User-visible behavior

1. Connect using the launcher token, upload the bundled fictional PDF, and select
   a ready document version.
2. Enter the problem, intended result, audience, requested report sections,
   constraints, and request type (problem/RFP/RFQ). Save the assignment.
3. Reload and reconnect to restore the persisted assignment and selected sources.
4. Choose **Preview mock report**. The server loads the saved assignment, retrieves
   eligible evidence, builds Jai's evidence map, and validates the returned report.
5. Click a citation to inspect the corresponding source text, page locator, chunk
   ID, and immutable document-version ID in Yasha's report viewer.
6. Editing assignment fields hides the prior report and disables preview until
   the changes are saved. Form controls are disabled during requests.

The browser no longer shows a hardcoded report unrelated to the assignment.
The original mock fixture is retained only for the component regression test.
A source gap returns an explanation with zero model-adapter calls. RFQ requests
without constraints return Jai's clarification questions.

## Implementation decisions

- Retained the Week 2 React 19/Vite 7 configuration, relative `/api` proxy, and
  Playwright suite. Added Yasha's Vitest/testing-library check alongside it and
  regenerated the combined npm lockfile. CI now runs that viewer check too.
- Extracted assignment controls into `AssignmentForm.tsx`; `App.tsx` coordinates
  persistence, uploads, search and report preview. `main.tsx` only mounts the app.
- Replaced the separate unauthenticated in-memory API with a compatibility import:
  `backend.api.main:app` and `backend.api.app:app` serve the same shared API.
- Added `POST /api/v1/assignments/{uuid}/consult`, which checks the saved assignment's
  owner and department before accessing evidence. The client cannot submit a
  replacement assignment or override access policy through this endpoint.
- Added `backend/engine/workspace.py`. Its repository narrows access to the saved
  assignment's department, honors selected versions, and never falls back to
  Jai's fixture repository. Its mock adapter quotes supporting chunks and returns
  their actual IDs. Jai's pipeline still validates sections and citations.
- Fixed Jai's word-budget guard so an oversized first chunk cannot bypass the
  450-word limit. Whole chunks are skipped rather than truncating source text.
- Added optional `AICORP_PORT` support for the launcher/browser tests, so tests can
  run without stopping an existing app on port 8000.
- Updated the API contract, OpenAPI snapshot, README, setup, and file walkthrough.
  Week 1 scripts/examples are marked historical; prior validation evidence is
  retained unchanged. Local `.env`, database contents, and bytecode are excluded
  from the integration commit.

## Boundaries

This remains a local fictional-data prototype. The mock report is an evidence
preview, not a live generated consulting recommendation. Reports are returned
for the current browser session and are not persisted. Comparable historical
cost records require an agreed population/date/source scope; this bridge returns
no records, so Jai's cost calculation produces null amounts and a reason. It does
not relabel his $12,000–$15,000 fixtures or Jonathan's aggregate spending as the
assignment's cost evidence. Live provider calls, production identity, report
version storage and a scoped historical-cost adapter remain future work.

## Validation

Run from the repository root:

```bash
.venv/bin/python -m pytest --run-data -q --tb=short
npm run build --prefix apps/web
npm run test:unit --prefix apps/web
AICORP_PORT=8011 .venv/bin/python scripts/test_week2_browser.py
```

Backend: **55 passed**, including existing financial/data/engine tests and new
report/citation, unauthorized caller, foreign owner, missing assignment,
unapproved evidence, evidence gap, RFQ clarification, department isolation and
context-budget checks. Frontend production build and the report-viewer unit test
passed. The only backend warning is the existing Starlette/httpx deprecation.
Browser: **2 passed** against a disposable PostgreSQL database on port 8011,
covering upload, save/reload, RFP persistence, search, report preview, clickable
citations, report invalidation after edits, corrupt PDFs, evidence gaps and API
outages. Local screenshots are in `evidence/local/` (not committed).
