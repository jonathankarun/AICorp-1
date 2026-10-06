# AICorp code handbook

A plain-language guide to the code that exists, the data it accepts, and the results it produces.

**Reviewed October 6, 2026.** The main-branch implementation described here is
`450122f1d86247465e66918162ceacdda6a7218f`. Documentation commits after that revision
may change this handbook without changing application behavior. Newer unmerged
team work is covered separately in [Branch additions](branches.md).

## Start here

AICorp is a local prototype for collecting a consulting assignment, attaching
traceable evidence, and testing a consulting-report engine. All committed example
data is fictional. The browser currently saves assignments, uploads PDFs, and
searches their text. On this version of `main`, report generation is a separate
Python engine; the browser does not call it.

Read the pages in this order, or jump directly to the question you have:

1. [System and workflows](workflows.md): what happens from a user's action to the database and back.
2. [Inputs and outputs](contracts.md): every model field, file input, result shape, default, and validation rule.
3. [HTTP API](api.md): all implemented endpoints, authentication, examples, and errors.
4. [Data storage](storage.md): database entities, relationships, audit records, and immutable evidence.
5. [Function reference](functions.md): every named Python function/method, frontend function, model, and SQL function, with source links.
6. [Running and troubleshooting](operations.md): setup, commands, configuration, test coverage, and recovery.
7. [Branch additions](branches.md): Jai's engine demos and Yasha's frontend/integration work not yet on `main`.
8. [Branch symbol inventory](branch-symbols.md): additional/changed Python functions and model fields on the fetched branches.

## Words used throughout this guide

- **Assignment:** the problem, desired result, audience, constraints, and sources a user saves.
- **Document:** a logical uploaded source. Its ID stays the same across revisions.
- **Document version:** one immutable snapshot of content and metadata. Citations should identify this version.
- **Chunk:** a small piece of extracted text from one PDF page.
- **Evidence:** chunks permitted for the current operation and relevant to the query.
- **Ingestion:** turning uploaded bytes into searchable, page-linked chunks.
- **Repository:** a Python boundary that reads or writes data; it is not an HTTP endpoint.
- **Adapter:** code that translates one interface to another, such as a saved response acting as a model.
- **Scope:** the department, sources, dates, and permissions that limit an operation.
- **RFP / RFQ:** request for proposal / request for qualifications; accepted request categories, not separate procurement systems.

## Source map

- [`apps/web`](../../apps/web): React/TypeScript interface, Vite build, Playwright browser tests.
- [`backend/api/app.py`](../../backend/api/app.py): FastAPI routes and local authentication.
- [`backend/data`](../../backend/data): PostgreSQL connections, migrations, CSV/PDF processing, persistence, search, validation.
- [`backend/engine`](../../backend/engine): assignment clarification, retrieval, mock generation, report validation.
- [`scripts`](../../scripts): setup, launcher, recovery, browser checks, evidence recording.
- [`contracts`](../../contracts): published JSON Schema, OpenAPI, and example payloads.
- [`tests`](../../tests): behavior checks and fictional fixtures.
- [`evaluation`](../../evaluation): labeled retrieval queries.
- [`evidence`](../../evidence): historical recorded results. These are records of earlier runs, not proof of a new run.

## What is and is not implemented

Implemented on `main`: a local bearer-token API, persistent assignments,
CSV payment staging/revision history, PDF ingestion, immutable evidence, PostgreSQL
keyword search, an injectable database evidence adapter, and a saved-response
consulting engine. There are no implemented `/projects`, `/reports`, `/sources`,
or `/consult` routes on this revision; the root README's planned architecture is
conceptual. There is no live LLM provider, production login, OCR, vector search,
report persistence, or deployed production service. See the branch guide for the
new consultation endpoint on `yasha-week2`.
