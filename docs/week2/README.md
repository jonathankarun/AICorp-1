# Week 2: usable data and frontend integration

Week 2 is October 4–10, 2026. This implementation connects a React/TypeScript
workspace to FastAPI, PostgreSQL, PDF ingestion, and the engine's evidence
adapter. All included data is fictional. It requires no paid model API.

## Start here

1. [Setup and demo](setup.md): exact commands and a presentation sequence.
2. [How the system works](explanation.md): concepts and a file-by-file walkthrough.
3. [Data and API contract](../../contracts/data/v2/README.md): fields, IDs,
   permissions, status transitions, errors, and examples.
4. [Validation evidence](../../evidence/week-2/jonathan/README.md): commands,
   expected/actual outcomes, retrieval baseline, and limitations.

## What is implemented

- Saved assignments and immutable document-version selections.
- A local UI for PDF upload, processing status, source selection, and search.
- Raw CSV/PDF preservation, source metadata, rejected-row reporting, and payment
  revision history.
- Exact decimal spending with a scope-matched budget; repeat imports are safe.
- Page-aware PDF extraction, immutable chunks, and keyword search with access
  and external-model permission checks.
- A real database evidence adapter for Jai's engine; evidence gaps stop before
  model generation.
- Twelve labeled retrieval cases: ten development cases and two held-out cases.
- Disposable-database API/data tests and real Chromium workflow tests.

The integrated UI combines Yasha's assignment/report workflow with the local
workspace and authenticated PostgreSQL API. Saved assignments can run through
Jai's Week 2/3 pipeline with database evidence and a local mock preview adapter.
See [integration details](frontend-integration.md) for changes and limitations.

## Boundaries that remain explicit

This is a local fixture demonstration, not City deployment. Real authentication,
City data approval, sponsor classification/budget decisions, teammate contract
signoff, independent teammate reproduction, and live-model comparison remain
human/external steps. No messages were sent to teammates and no paid model calls
were made. Generated report quality is not established by retrieval tests.

The demo's access policy is department-scoped. Public means the document's
source classification; it does not bypass department membership. Unknown source
access is excluded from usable-source lists and search. Read permission and
external-model permission are separate checks. Real object storage, robust job
workers, advanced OCR, and semantic retrieval remain later work.
