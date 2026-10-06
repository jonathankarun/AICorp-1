# Explaining the Week 2 implementation

## A short explanation you can say aloud

“Week 1 gave us a rebuildable database and a mock engine. In Week 2 I added the
path that gets usable data into that database. The frontend now saves assignments
through an API and uploads PDFs. The backend preserves the original files,
extracts text with page locations, and marks a document ready only after its
chunks are stored. The engine can search those chunks through a shared interface.

“For financial data, I added a CSV importer that checks each row, preserves bad
rows with reasons, prevents repeat imports from duplicating payments, and records
corrections. The controlled example produces $280 of consulting spending and a
2.8% share of a matching $10,000 budget. The $50 we cannot classify stays separate.

“The integration runs locally with fictional records. We measured keyword
retrieval instead of assuming it works: six of seven answerable development
queries found the right document. We still need team signoff, real data approval,
and authorized live-model evaluation.”

## The two main paths

- `backend/engine/workspace.py`: bridges the shared database search to Jai's
  Week 2/3 repository protocol and produces a labeled mock evidence preview.
  The authenticated assignment `consult` route returns validated report citations
  and the exact evidence used. It does not fabricate comparable cost records.

### Frontend and documents

1. **Browser:** React keeps the assignment fields, selected source IDs, upload
   progress, and error messages in component state. It sends HTTP requests.
2. **API:** FastAPI validates input shapes and derives the caller's access context
   from the configured local identity after token authentication.
3. **Repository operations:** SQL saves the assignment, checks selected versions,
   and returns only accessible records. The browser never executes SQL.
4. **Submission:** original PDF bytes and metadata are saved with a generated job
   and document ID. The response is pending; storing bytes is not extraction success.
5. **Processing:** the worker reads the PDF page by page. Empty/scanned pages fail
   visibly. Text is split into chunks that never cross a page boundary.
6. **Ready:** chunks and an immutable document version are saved together. Only
   then does the job become ready. The UI polls and offers the source for selection.
7. **Retrieval:** PostgreSQL matches/ranks keywords after filtering access,
   readiness, selected versions, and external-model permission.
8. **Engine:** the adapter deduplicates passages and limits total characters.
   Each passage retains its version ID and page locator. No evidence stops generation.

### CSV and money

1. Preserve original bytes and the source manifest.
2. Stage each CSV row, retaining its original field text and row number.
3. Normalize whitespace, dates, decimal amounts, and known entity names/keys.
4. Reject malformed/ambiguous records with a reason instead of silently dropping them.
5. Identify each payment by source namespace and transaction ID. Use a conservative
   composite fallback only when the source lacks an ID.
6. Insert a new payment, leave an identical one unchanged, or record an explicit-ID
   correction with before/after values.
7. Aggregate only the declared source population, department, dates, and currency.
   Check the budget uses the same scope before calculating the percentage.

## File-by-file guide

### Database and data code

- `backend/data/migrations/002_week2.sql`: extends the schema without editing the
  checksummed Week 1 migration. `assignments` stores actor, department, and the
  typed JSON payload; `assignment_sources` links saved selections to real versions.
  `documents` stores document identity/ownership. `ingestion_jobs` stores raw PDF
  bytes, metadata, status, errors, and the resulting version. `source_imports`
  preserves raw CSV exports and manifests. `import_rows` records every staged row's
  outcome. `payment_revisions` records corrections. `search_runs` logs queries,
  filters, and returned IDs. A nullable payment department supports spending for
  rows whose engagement is unknown.
- `backend/data/week2_models.py`: Pydantic contracts for assignments, documents,
  and searches. Rejects extra fields, invalid UUIDs, blank required strings,
  invalid enum values, and unsupported limits. Unknown access cannot claim model
  approval. The same types drive API validation and generated schemas.
- `backend/data/workspace.py`: authorization and assignment/document repository
  operations. `save_assignment` validates source selections, saves the assignment,
  and creates source relationships in a transaction. `get_assignment` requires
  owner and department access. Source/job lists apply department filters.
  `DataError` carries a stable error code and HTTP status for the adapter.
- `backend/data/ingestion.py`: checks size and PDF signature, saves original bytes,
  extracts pages, splits passages, creates hashes/IDs, and advances job status.
  It locks the document row while assigning versions so concurrent workers cannot
  create conflicting versions. Identical content/provenance reuses the version;
  changed content/provenance appends one. Failed extraction creates no usable version.
- `backend/data/importer.py`: stages/cleans CSV records; matches existing entities;
  checks exact currency amounts; detects identity collisions; inserts, skips, or
  revises payments; preserves raw/rejected rows. `spending` checks budget scope and
  returns consulting, operational, unresolved, and consulting share separately.
  An advisory transaction lock serializes imports to prevent conflicting upserts.
- `backend/data/search.py`: PostgreSQL English full-text keyword baseline. It
  builds a parameterized OR query, filters permitted ready versions, ranks results,
  adds page locators, and logs query/result IDs. No vector index or embeddings.
- `backend/data/week2_cli.py`: data-owner command for importing an actual CSV and
  manifest into the configured database and writing a JSON report. Exit code 2
  means at least one row was rejected; valid rows remain imported and auditable.
- `backend/data/week2_demo.py`: fresh-database financial and retrieval demonstration.
  Seeds known entities, imports twice, exercises a rejection, creates approved and
  forbidden corpus variants, saves an assignment, and evaluates development queries.
  Writes actual IDs, totals, hashes, and relevance results. Drops its test database.
- `backend/data/export_week2_contracts.py`: generates input JSON Schemas, an example
  assignment, and OpenAPI. Contract tests catch stale generated files.
- `backend/data/validate.py` (updated): retains Week 1 checks but expects the current
  migration set on an empty database. The Week 1 two-payment total remains $300.

### API and engine

- `backend/api/__init__.py`: marks the API package.
- `backend/api/app.py`: local authentication, startup guard, assignment routes,
  document upload/list/status, search, safe error responses, and built frontend
  hosting. Accepted uploads run extraction as a background task using a fresh
  connection. The approved fixture hash governs outbound eligibility, not a client
  checkbox. The factory permits isolated test connections without real credentials.
- `backend/engine/retrieval.py`: callable `DataEvidenceRepository` adapter. Converts
  assignment text into a search, intersects the assignment department with the
  actor's memberships, applies selected-version filters, deduplicates
  chunk hashes, enforces the context character budget, and maps database records
  to Jai's existing `EvidenceChunk` model. UUIDs become JSON/Python strings; page
  numbers become locators such as `page 1`.
- `backend/engine/pipeline.py` (updated): accepts an optional evidence repository.
  Existing Week 1 callers still use the mock. Real retrieval can return
  `needs_input` before a model call or a structured invalid-retrieval error.
  Report/citation validation remains in place.

- `backend/engine/workspace.py`: bridges the shared database search to Jai's
  Week 2/3 repository protocol and produces a labeled mock evidence preview.
  The authenticated assignment `consult` route returns validated report citations
  and the exact evidence used. It does not fabricate comparable cost records.

### Frontend

- `apps/web/package.json`: React/Vite/TypeScript dependencies and build/test commands.
- `apps/web/package-lock.json`: exact resolved JavaScript dependency versions.
- `apps/web/tsconfig.json`: strict TypeScript compilation settings.
- `apps/web/vite.config.ts`: development API proxy to localhost:8000.
- `apps/web/index.html`: page shell and React entry point.
- `apps/web/src/main.tsx`: mounts `App.tsx`.
- `apps/web/src/App.tsx`: the integrated workspace: token connection, assignment
  form, PDF input, job polling, ready-source checkboxes, persistence/reload, and
  evidence search. It sends only permitted input fields. Failed uploads or saves
  do not clear form state. It displays retrieved text as escaped React text.
  The token stays in session storage; only the last assignment ID is in local storage.
- `apps/web/src/components/AssignmentForm.tsx`: controlled assignment fields,
  required report sections, request type, and ready source selection.
- `apps/web/src/components/ReportView.tsx`: Yasha's report sections, citation buttons,
  source details, review needs, and explicit missing cost evidence.
- `apps/web/src/style.css`: responsive two-column layout, typography, inputs,
  status/error displays, focus indicators, and narrow-screen layout.
- `apps/web/playwright.config.ts`: browser test settings and real API startup.
- `apps/web/tests/workspace.spec.ts`: Chromium checks for upload → ready → selection
  → save → reload → search, corrupt PDF handling, evidence gaps, and preservation
  of form data during an API outage. The outage is intentionally simulated; the
  main success path uses the real API and database.

### Fixtures and evaluation

- `tests/fixtures/week2/payments.csv`: five controlled payments: 100, 200, -20,
  500, and 50 dollars, with explicit identities/classifications/rationales.
- `tests/fixtures/week2/manifest.json`: source identity, issuer/date/location,
  fiscal interval, access classification, and PDF metadata. Fictional provenance
  is explicit rather than presented as City evidence.
- `tests/fixtures/week2/budget.json`: the $10,000 denominator and its exact scope.
- `tests/fixtures/week2/engagement.pdf`: two-page, text-readable fictional engagement.
  Page 1 covers the six-week timeline; page 2 covers requested deliverables.
- `evaluation/week2_queries.json`: twelve labeled query cases covering literal
  matches, alternate wording, ambiguity, no evidence, and forbidden sources.
  Ten are development cases; two are held out from the baseline runner.
- `tests/test_week2.py`: PostgreSQL/data/API/engine regression tests, including
  concurrent processing, restart persistence, version preservation, import
  corrections/collisions, failed extraction, safe permissions, and schema drift.

### Commands, contracts, and evidence

- `scripts/create_week2_fixtures.py`: deterministically generates the PDF using
  ReportLab. Fixed metadata makes rebuilding the same content reproducible.
- `scripts/serve_week2.py`: migrates/seeds the working database, generates the local
  demo token, and starts the API on loopback. It requires a built frontend.
- `scripts/resume_uploads.py`: resumes pending/interrupted jobs after the API stops.
- `scripts/test_week2_browser.py`: creates a disposable database and runs browser
  tests against it, then cleans up. It has a main guard so pytest can import safely.
- `contracts/data/v2/*.schema.json`: generated assignment/document/search schemas.
- `contracts/data/v2/assignment.example.json`: a valid copyable assignment request.
- `contracts/data/v2/openapi.json`: generated HTTP contract.
- `contracts/data/v2/README.md`: semantics that schemas cannot fully express:
  ownership, readiness, filter combinations, errors, versioning, and financial scope.
- `requirements.txt` / `requirements.lock`: declared Python dependencies and exact
  installed versions, including PDF extraction, API, testing, and fixture generation.
- `.gitignore`: excludes environments, secrets, frontend builds/dependencies,
  transient test traces, and local evidence.
- `.github/workflows/tests.yml`: automatically runs backend/data checks, the demo,
  frontend build, and browser tests against a PostgreSQL service on GitHub.
- `docs/week2/`: setup, architecture, explanation, and handoff guide.
- `evidence/week-2/jonathan/`: expected results recorded before tests, actual command
  logs, demo JSON, source revision/fingerprint information, and browser screenshot.
- `README.md`: points new teammates to Week 2 and preserves Week 1 instructions.

## Concepts a TA may ask about

**Why decimals instead of floating point?** Binary floating point cannot represent
many decimal fractions exactly. Money uses Python `Decimal` and PostgreSQL
`NUMERIC(18,2)`. The refund is negative and participates in the sum normally:
100 + 200 - 20 = 280. The budget share is 280 / 10000 × 100 = 2.8%.

**Why not classify a vendor once?** One firm can sell both consulting and operating
services. Classification belongs to a payment/engagement with rationale. The
unresolved $50 is preserved rather than guessed into consulting.

**What is idempotency here?** Re-importing the same source transactions has no
additional effect on payment counts/totals. Import attempts are still recorded.
This guarantee applies to CSV data, not all assignment POST requests.

**Why immutable versions?** If an assignment points at “the latest document,” a
later upload could change the evidence underneath it. A saved version ID pins
specific bytes/text. Processing state changes in a separate table.

**What is a hash?** SHA-256 produces a content fingerprint. It helps identify
unchanged bytes/text. It does not establish truth or permission by itself. The
local API's allowlist is a deliberate fixture-only approval policy.

**What is a transaction?** A set of database changes commits together or rolls
back. An assignment and its selections are atomic; evidence chunks and ready
status are atomic. The job's earlier pending/processing state remains durable.

**Why are uploaded and ready different?** Receiving bytes does not mean the file
can be read. Corrupt/encrypted/scanned PDFs can fail later. The UI must show the
result of processing rather than equating successful transport with usable data.

**What does top-five relevance measure?** Whether a labeled relevant document
appears among the first five ranked chunk results. It measures retrieval, not
factual correctness of generated reports. The tiny synthetic corpus is a baseline,
not evidence that the system meets City-user quality needs.

**Why did a query fail?** Keyword stemming handles some word variants but does not
infer that “turnaround bottlenecks” means “service delays.” The failed query is
recorded before considering semantic search. The two holdout queries are not used
for tuning.

**How does permission work?** Trusted server context gives department membership.
SQL filters candidate evidence before ranking. External-model permission is a
second restriction. A source can be readable yet excluded from model context.
No UI value can grant membership or approve an arbitrary upload for external use.

**Where are the original files?** PostgreSQL stores raw PDF and CSV bytes for this
small prototype. UUIDs identify uploads; filenames are display metadata only.
Object storage and a durable distributed worker would be later scaling changes.

**What happens if a worker crashes?** The job remains pending/processing in the
database. The explicit recovery script resumes it after the API stops. This is
not yet an automatic distributed queue with retries and timeouts.

**What is still a mock?** Week 1's default model adapter and evidence path remain
available. The new data adapter is real, but the validation model is a capture
mock used to prove which evidence is sent. No live model comparison was run.
