# Running, configuration, and verification

[Handbook home](README.md)

Run commands from the repository root. Tested setup targets Python 3.12/3.13,
Docker Desktop, PostgreSQL 17, and Node 22 in CI. Do not confuse commands that
operate on your configured database with validation commands that create a
separate temporary database.

## Start the application

```bash
python3 scripts/setup_local.py
npm ci --prefix apps/web
npm run build --prefix apps/web
.venv/bin/python scripts/serve_week2.py
```

Visit `http://127.0.0.1:8000`, enter the printed token, and upload
`tests/fixtures/week2/engagement.pdf`. Save an assignment, reload/reconnect, and
search `permit intake`. On Windows the virtual-environment executable is
`.venv/Scripts/python.exe`. Existing `.env` and database volumes are preserved by
setup. `npm run dev --prefix apps/web` starts Vite with `/api` proxied to port 8000;
the backend still needs to run.

## Configuration inputs

`connect()` loads the root `.env` without overriding existing environment values.
Application settings passed directly to `create_app()` take precedence over its
environment-derived defaults.

- `POSTGRES_PASSWORD`: required; the example placeholder is rejected. Setup generates a random local password when creating `.env`.
- `POSTGRES_USER`: defaults to `aicorp`.
- `POSTGRES_DB`: defaults to `aicorp`; test tools override it for isolation.
- `POSTGRES_PORT`: defaults to `55432` in Python/local Compose usage; CI uses `5432`.
- `PGHOST`: defaults to `127.0.0.1`.
- `AICORP_LOCAL_DEMO`: must be `1` for API startup; launcher sets it.
- `AICORP_DEMO_TOKEN`: at least 16 characters; launcher generates one if absent. This is a local shared token, not per-user identity.
- `AICORP_MAX_UPLOAD_BYTES`: integer; default `10485760` (10 MiB).
- `AICORP_PYTHON`: browser-test configuration uses this to choose the Python executable.
- `AICORP_PORT`: supported only on the unmerged integrated branch, not this `main` launcher.

See [Compose](../../compose.yaml), [environment template](../../.env.example), and
[browser configuration](../../apps/web/playwright.config.ts) for deployment/test
wiring. Never commit the real `.env`, tokens, database contents, or generated caches.

## Data commands and outputs

```bash
.venv/bin/python -m backend.data.cli migrate
.venv/bin/python -m backend.data.cli seed
.venv/bin/python -m backend.data.cli lookup 30000000-0000-4000-8000-000000000001 \
  --actor-id 50000000-0000-4000-8000-000000000001 \
  --department-id 10000000-0000-4000-8000-000000000001
.venv/bin/python -m backend.data.week2_cli import-csv \
  tests/fixtures/week2/payments.csv tests/fixtures/week2/manifest.json \
  --output evidence/local/import.json
```

These commands operate on the configured database. `migrate` prints applied
filenames; `seed` prints inserted counts. Lookup prints a typed engagement or
not-found result. Data CLI exit codes are 0 success, 2 not found, and 1 caught
configuration/database failure. The import CLI writes/prints row results and
returns 2 if any row was rejected, otherwise 0; uncaught input/file errors fail
normally. Caller-supplied CLI identities are test inputs, not authentication.

## Engine command and outputs

```bash
.venv/bin/python -m backend.engine.runner \
  tests/fixtures/assignment_complete.json \
  --output evidence/local/engine-result.json
```

Optional `--mock-response PATH` defaults to `tests/fixtures/mock_report.json`.
The assignment positional argument is required. Default output is
`engine_result.json` if `--output` is omitted. The command writes structured JSON,
prints the result and destination, and exits 1 for typed engine errors or 0 for
reports/clarification requests. File reading and malformed JSON errors are not
converted to the engine's typed error envelope.

## Recovery

- Wrong token: reconnect with the current launcher's token. Restarting with a newly generated token invalidates the old one.
- Database unavailable: restore Docker/PostgreSQL and verify configuration, then retry. The UI reports a friendly error; `/health` alone cannot verify recovery.
- Upload still pending/processing after interruption: stop the API, run `.venv/bin/python scripts/resume_uploads.py`, then restart. It processes durable pending/processing jobs and prints IDs/states.
- Failed PDF: inspect the job error. Replace scanned, encrypted, unreadable, or oversized input and upload again; failed jobs are not retried by recovery.
- No search results: check query words, selected versions, readiness, department access, and outbound-model approval. Readable does not mean approved for external use.
- Seed conflict: investigate the existing record; seeding refuses to overwrite a changed fixture silently.
- Changed migration checksum: restore the historical migration and add a new migration for intentional changes.
- Missing frontend: run the frontend build before starting the launcher.

## Tests and recorded evidence

```bash
# Includes integration tests; requires reachable PostgreSQL and CREATEDB capability.
.venv/bin/python -m pytest --run-data -q
.venv/bin/python -m backend.data.validate
.venv/bin/python -m backend.data.week2_demo
npm run build --prefix apps/web
npm exec --prefix apps/web -- playwright install chromium
.venv/bin/python scripts/test_week2_browser.py
```

Without `--run-data`, database integration fixtures skip their tests. This does
not prove database behavior. `empty_test_database()` creates a random database
and removes only that database in cleanup. Backend validators/browser wrappers
use disposable databases rather than resetting the configured development DB.

- `tests/test_data.py`: migrations, repeatable seed, exact money/refunds, foreign keys, authorization, immutable evidence.
- `tests/test_data_contracts.py`: generated v1 contracts equal committed contracts.
- `tests/test_engine.py`: valid report, invalid citation output, RFQ clarification before a model call.
- `tests/test_week2.py`: CSV identity/corrections/rejections, scoped spending, PDF versioning/failures/recovery/concurrency, assignment persistence, API authorization, outbound permissions, evidence gaps, context limits/deduplication, and v2 contract snapshots.
- `apps/web/tests/workspace.spec.ts`: real-browser persistence, upload/search, and failure behavior.
- `.github/workflows/tests.yml`: runs backend tests, validators/demo, frontend build, and Chromium browser tests on push/PR.

The Week 1 validator defaults to `evidence/local/week1-validation.json`; it records
checks, fixture version, source fingerprint, commit, platform, and database
version. The Week 2 demo defaults to `evidence/local/week2-demo.json` and records
spending, retrieval baseline, fixture hash, and source commit. Its holdout queries
are explicitly not run. `scripts/record_week1_evidence.py` captures Week 1 evidence;
`scripts/create_week2_fixtures.py` regenerates the synthetic PDF fixture.

## Regenerate contracts

```bash
.venv/bin/python -m backend.data.export_contracts
.venv/bin/python -m backend.data.export_week2_contracts
```

These overwrite the committed contract artifacts with current model/schema
output. Review the diff before committing. The function/model inventories in this
handbook were extracted from source and annotated during this documentation pass;
update them when code changes. Snapshot dates and branch commit IDs are deliberate
so readers can distinguish historical evidence from current behavior.

## Verification of this documentation update

On October 6, 2026, the documentation pass checked 106 local Markdown links,
coverage of all implemented main-branch API paths, and inventory coverage of all
121 named Python functions/methods in tracked backend, script, and test files.
The following focused checks passed: **5 tests**.

```bash
.venv/bin/python -m pytest tests/test_engine.py tests/test_data_contracts.py \
  tests/test_week2.py::test_exported_week2_contracts_match -q
```

There was one existing Starlette/httpx deprecation warning. No application code
was changed. Full PostgreSQL/browser suites and unmerged-branch suites were not
rerun for this documentation-only update; earlier branch test results are labeled
historical in the branch guide.
