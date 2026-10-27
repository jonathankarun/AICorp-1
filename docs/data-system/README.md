# My data subsystem — how to run and explain it

This is Jonathan's local data subsystem. It stores records, imports payments and
PDFs, finds evidence and comparable work, calculates spending, preserves reports
and citations, records reviews/corrections, and proves that backups restore.
The browser is deliberately basic. All bundled records are fictional.

## Start it

From the `AICorp-1` folder, with Docker Desktop running:

```bash
python3 scripts/setup_local.py
npm ci --prefix apps/web
npm run build --prefix apps/web
.venv/bin/python scripts/serve_week2.py
```

Open http://127.0.0.1:8000. Paste the token printed in the terminal and click
**Connect**. The launcher name is kept for compatibility; it now starts the whole
data demo. It applies new migrations, seeds the example, and gives the local demo
actor administrator permission. Restarting does not reset reviewed payments.
Stop the server with Ctrl+C. PostgreSQL keeps its data in the Docker volume.

## The simple demo

1. Click **Load spending**. A fresh example shows $280 consulting, $500 operational,
   $50 unresolved, and 2.80% of a matching $10,000 October budget. The $280 includes
   the -$20 refund. These are exact decimal amounts, not rounded floating-point sums.
2. Enter a reason and click **Classify the unresolved $50 as consulting**. Consulting
   becomes $330, unresolved becomes $0, and the percentage becomes 3.30%. The saved
   correction shows the old/new categories, actor, reason, and time. Reload and
   reconnect to show persistence. If it already says $330, the correction was saved
   during an earlier demo; that is expected, not a failed reset.
3. Search comparable work for `process`. You get the project, vendor, specialty,
   evidence pages, payment totals, and an explicitly unknown outcome. Project
   payments include the separate Week 1 fixture as well as the Week 2 export;
   these totals are intentionally a different population from the October panel.
4. In **Find evidence**, search `timeline`. The source passage says six weeks and
   identifies page 1. Click **Open original PDF** to see the actual saved source.
   You can also upload your own readable PDF, wait for `ready`, and search its text.
   Searching here is local; it does not call an AI model.
5. To update a source, choose it in **Document version** before uploading. Same
   bytes and metadata reuse the version; changed bytes/configuration make a new
   version. Old versions remain available. Selecting **New document** intentionally
   creates a separate document, even if another document has the same bytes.

Assignments can still be saved and restored. The UI demonstrates three main
capabilities; report storage/reviews and administrative access changes are exposed
through the API and acceptance checks rather than extra screens.

## Verify everything

```bash
.venv/bin/python scripts/validate_data.py --disposable --browser
.venv/bin/python -m backend.data.benchmark
```

The validation command exits unsuccessfully if a check fails. It runs the full
Python suite, builds the frontend, then uses a real browser. Tests create and
remove random temporary databases; they never reset your working database.
Browser checks require Playwright Chromium (`cd apps/web` then
`npx playwright install chromium` if it is missing).
Results go in `evidence/local/data-acceptance.txt`, `data-build.txt`, and
`data-browser.txt`. The screenshot is `evidence/local/data-demo.png`.
The benchmark stores all 30 before/after timings, result IDs, query plans, machine,
PostgreSQL version, dataset counts, import duration, and database size. It uses
10,000 extra synthetic chunks in a temporary database. It checks that indexing
returns exactly the same results. Timings are a local sample, not a service promise.

Acceptance coverage lives in `tests/test_data.py`, `test_week2.py`, `test_week3.py`,
and `test_release.py`: empty migrations and upgrades, repeat imports, invalid rows,
refunds, deduplication, source versions, permission denials, citations, concurrent
report writes, corrections, reviews, recovery, and extraction configuration changes.

## Back up and prove recovery

```bash
.venv/bin/python -m backend.data.recovery backup evidence/local/my-backup
.venv/bin/python -m backend.data.recovery verify evidence/local/my-backup
```

Choose a new directory each time. Backup uses one PostgreSQL snapshot, so rows and
the dump describe the same moment even if writes continue. Original PDFs and CSVs
are inside the database, so they are included. The manifest records table counts,
row hashes, schema hashes, application hashes, database version, and dump checksum.
Copy the whole directory to your backup location. Keep the matching application
checkout and lockfiles too; the backup records their identity, not their source code.

Verification restores into a NEW temporary database, checks every table's contents,
and removes only that database afterward. It never overwrites the working database.
The helper uses `pg_dump`/`pg_restore` inside this project's local Docker Compose
PostgreSQL container; remote databases need an operator-managed equivalent.

## Maintenance

- Import a payment export with `.venv/bin/python -m backend.data.week2_cli import-csv tests/fixtures/week2/payments.csv tests/fixtures/week2/manifest.json --output evidence/local/import.json`.
  The CLI is a trusted local operator tool, not an unauthenticated web endpoint.
  Follow that fixture's headers and manifest. Rejected rows retain their original
  values and explanations. Nonzero exit status means rows need review.
- A reviewed classification takes priority over later CSV classifications. CSV
  source bytes are retained, while the effective category stays at the reviewer's
  decision. Change it again through the correction endpoint with a new reason.
- Upload a readable PDF through the UI/API. Image-only, encrypted, oversized, and
  corrupted PDFs get a specific error. There is no OCR or embedding service.
- Resume interrupted pending/processing uploads with `scripts/resume_uploads.py`.
  Failed extraction needs a corrected file, not an endless automatic retry.
- If extraction or chunk sizing changes, change `EXTRACTION_VERSION` in
  `backend/data/ingestion.py` and resubmit against the same document ID. It creates
  new evidence while old citations keep the original chunks. Rebuild the text
  index with PostgreSQL REINDEX only if the index itself needs maintenance.
- Use the access endpoint to block a document without deleting its bytes. Search,
  direct PDF/chunk access, comparable evidence, and cited reports all recheck it.
- Never edit applied SQL migrations. Add a new numbered migration; old checksums
  deliberately reject rewritten history.

## Permissions and report workflow

The local API accepts one server-configured bearer token and actor. Request bodies
cannot choose their actor or grant themselves roles. Department membership controls
reads. A reviewer role can correct payments and review their accessible owned
reports. An administrator can also block/unblock documents. Roles live in
`data_roles` and are provisioned by trusted setup, not by a public endpoint.
A plain reader cannot perform these operations. An administrator still cannot read
another department just because they have that role.

Report storage currently keeps reports private to their owning actor. Team-shared
review queues and real user login belong to the shared application integration.
New report versions must be drafts. Reviews are append-only and tied to an exact
version: `reviewed` can lead to `approved`; `changes_requested` or `approved` closes
that version's review workflow. Further work uses a new draft version. Expected
revision/category checks reject stale edits instead of silently overwriting them.

Blocking a document blocks reports citing that document. Stored bytes, prior
reviews, and financial history remain intact. External-model eligibility remains
separate from human read access. The API never lets an arbitrary uploaded PDF grant
itself model permission; only the known fictional PDF is allowlisted.

## API and data shapes

See http://127.0.0.1:8000/docs and the generated
`contracts/data/v2/openapi.json` for the actual request shapes. Existing `/api/v1`
paths remain compatible; the OpenAPI document is now release 4.0. Protected requests
need `Authorization: Bearer <your local token>`.

New routes cover `POST /comparables`, `POST /facts`, `GET /chunks/{id}`,
`GET /documents/{version_id}/pdf`, `POST /documents/{document_id}/access`,
`GET /demo/spending`, `POST /payments/{id}/classification`, `POST /reports`,
`GET /reports/{id}/{version}`, and `POST /reports/{id}/{version}/reviews`, all under
`/api/v1`. The spending demo uses the checked-in budget; general spending calculations
remain available through `backend.data.importer.spending` with an explicit matching
budget/population/date range. API errors use `error.code` with 401, 403, 404, 409,
422, or 503 as appropriate.

Existing field dictionaries: `docs/reference/storage.md`, `docs/reference/contracts.md`,
and `docs/week1/schema.md`. New fields:

- `data_roles.actor_id` is the server actor UUID; `role` is reviewer or administrator.
- `document_restrictions.document_id` identifies all versions of one source;
  `blocked` is a boolean and `revision` is a positive integer for stale-write checks.
- `data_audit.audit_id` is an increasing event ID; `actor_id` identifies the changer;
  `resource_id` identifies the payment or document; `action` names the operation;
  `old_value`/`new_value` preserve JSON values; `reason` is required text;
  `created_at` is a timezone-aware database timestamp. Events cannot be rewritten.
- `report_reviews.report_version_id` is the exact immutable report version UUID;
  `revision` counts review events for that version; `actor_id`, `decision`, `reason`,
  and `created_at` explain each decision. A new version starts with no review events.
- Money remains decimal USD for the fixture importer. Budget dates are inclusive.
  Unknown outcomes remain null with an explanation, never invented success.

## What is still outside this local release

Real City records and permission policy, real identity-provider login, production
hosting/operations, teammate reproduction/sign-off, and live AI generation are not
claimed complete. No teammate was contacted, no release tag was created, and no
remote deployment was performed. Semantic/vector search stays deferred until a
model/configuration and a measured need are agreed. Keyword search is implemented
and indexed. This is an independently usable local data subsystem, not the entire
team's production application.
