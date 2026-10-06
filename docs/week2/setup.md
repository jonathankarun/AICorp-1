# Week 2 setup and demonstration

Run commands from the repository root. Use Python 3.12 or 3.13, Node 22, and
Docker Desktop. Existing database contents and `.env` are preserved.

## Install and launch

```bash
python3 scripts/setup_local.py
npm ci --prefix apps/web
npm run build --prefix apps/web
.venv/bin/python scripts/serve_week2.py
```

Open http://127.0.0.1:8000 and enter the local demo token printed by the launcher.
The launcher generates a fresh token each start unless `AICORP_DEMO_TOKEN` is
already set. It binds only to loopback. The default app refuses startup unless
local-demo mode is explicitly enabled and the token is at least 16 characters.
Do not configure this test identity for a shared deployment.

The API and built frontend share one origin. For frontend development, run the
API and `npm run dev --prefix apps/web`; Vite proxies `/api` to port 8000. There
is one relative API prefix in the client, with no provider secret in the bundle.

## A five-minute demonstration

1. Connect with the demo token. Enter problem **Improve permit intake**, intended
   result **A preliminary improvement plan**, and a six-week constraint.
2. Upload `tests/fixtures/week2/engagement.pdf`. The API returns an ID and pending
   status, then processes the file. Polling shows ready when extraction commits.
   Small files may finish before the next poll, so intermediate states can be brief.
3. Select the ready source and save the assignment. Reload, reconnect, and show
   that both the assignment fields and selected version remain saved.
4. Search **timeline**. Explain that the result includes page 1 and a stable
   version/chunk ID. Search **deliverables** to see page 2.
5. Search **quasar spectroscopy** to demonstrate an evidence gap.
6. Upload a corrupt `.pdf` to show failed status and corrective guidance. The
   assignment form remains intact. A non-PDF is rejected before creating a job.
7. In another terminal, run the financial/retrieval demonstration below. Show
   five inserted payments, five unchanged on repeat import, and the exact totals.

Only the exact bundled fictional PDF hash is automatically eligible for external
model context through the local HTTP adapter. Other readable PDFs can be saved
and selected, but the model-context search excludes them pending approval. The
frontend explicitly labels this distinction. Upload metadata cannot grant itself
external-model permission.

## Validation

```bash
.venv/bin/python -m pytest --run-data -q
.venv/bin/python -m backend.data.validate
.venv/bin/python -m backend.data.week2_demo
npm exec --prefix apps/web -- playwright install chromium
.venv/bin/python scripts/test_week2_browser.py
```

Stop an existing demo server before running the browser suite; it reserves port
8000 and refuses to attach to an unrelated server. The browser runner creates a
random test database, migrates/seeds it, starts the real API, and removes that
database afterward. Data/API tests and both demonstration commands also use
fresh temporary databases. They do not clear your local working database.

The Week 2 demo writes `evidence/local/week2-demo.json`. It preserves generated
IDs, query results, financial output, PDF hash, source commit, and the retrieval
baseline. The frozen submitted evidence is under `evidence/week-2/jonathan/`.

## Custom CSV import

The importer is currently a Python/CLI data-owner workflow, not a browser CSV
upload. Use the exact published CSV headers and a source manifest:

```bash
.venv/bin/python -m backend.data.week2_cli import-csv path/to/payments.csv path/to/manifest.json --output evidence/local/import.json
```

This imports into your configured local database. Unknown aliases and malformed
rows are retained as rejections. Inspect the report before accepting a dataset.
Reusing an explicit transaction ID in the same source namespace updates that
payment with old/new revision history. It does not delete payments absent from a
later file. A fallback composite identity cannot safely identify a correction
that changes the composite itself; resolve that case manually with a stable ID.

## Recovery and configuration

- Database unavailable: start Docker Desktop, then `docker compose up -d --wait`.
- Interrupted upload: stop the API, run `.venv/bin/python scripts/resume_uploads.py`,
  then restart. This resumes pending/processing jobs and preserves ready/failed
  jobs. For a failed file, upload a corrected file; failed jobs remain evidence.
- Upload limit: set `AICORP_MAX_UPLOAD_BYTES`; default 10 × 1024 × 1024 bytes.
  UI guidance shows the default; the server enforces the actual configured limit.
- PDF limits: 100 pages, 500,000 extracted characters, 1,200 characters/chunk.
  Any blank/scanned page requires review; automatic OCR is not implemented.
- Old document updates: the internal document contract accepts `document_id` to
  append a version. The simple UI creates new documents for uploads. Existing
  assignments continue to reference the original immutable version.
- Rebuild contracts: `.venv/bin/python -m backend.data.export_week2_contracts`.
- Rebuild the fixture: `.venv/bin/python scripts/create_week2_fixtures.py`.
