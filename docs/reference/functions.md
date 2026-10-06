# Function and class reference

[Handbook home](README.md)

This source-derived inventory covers every named Python function/method and class in tracked backend, script, and test files at the documented main revision. Signatures show exact parameter defaults and annotations; unannotated results are explained in prose. Model fields are listed in [Inputs and outputs](contracts.md). Nested route handlers are included. Anonymous callbacks are described with their containing frontend workflow.


## backend/__init__.py

[Open source](../../backend/__init__.py)

No named functions/classes. Package marker or module-level definitions only.


## backend/api/__init__.py

[Open source](../../backend/api/__init__.py)

Local Week 2 HTTP integration adapter.

No named functions/classes. Package marker or module-level definitions only.


## backend/api/app.py

[Open source](../../backend/api/app.py)

Authenticated local demo API. Real identity-provider integration is deferred.


### `create_app`

```python
create_app(connection_factory=connect, *, context=None, token=None, local_mode=None, max_bytes=None)
```

Build and return the configured FastAPI application; register authentication, error handlers, routes, and optional static frontend.


### `create_app.lifespan`

```python
create_app.lifespan(app)
```

Validate local mode and token before serving; raises RuntimeError for unsafe/missing configuration.


### `create_app.identity`

```python
create_app.identity(authorization: str | None=Header(default=None))
```

Read the Authorization header and return trusted AccessContext, or raise unauthorized (401).


### `create_app.domain_error`

```python
create_app.domain_error(request, exc)
```

Convert DataError to an HTTP JSONResponse with its code and status.


### `create_app.validation_error`

```python
create_app.validation_error(request, exc)
```

Convert request validation errors to HTTP 422 and dotted invalid-field paths.


### `create_app.database_error`

```python
create_app.database_error(request, exc)
```

Convert PostgreSQL errors to HTTP 503 without exposing driver details.


### `create_app.health`

```python
create_app.health()
```

Return the local-demo liveness dictionary; does not query PostgreSQL.


### `create_app.create_assignment`

```python
create_app.create_assignment(data: AssignmentInput, ctx=Depends(identity))
```

Accept AssignmentInput and trusted context; open a connection and return the newly persisted assignment.


### `create_app.read_assignment`

```python
create_app.read_assignment(identifier: UUID, ctx=Depends(identity))
```

Accept an assignment UUID and return its authorized saved payload, or not_found.


### `create_app.documents`

```python
create_app.documents(ctx=Depends(identity))
```

Return all ready, visible document versions for the trusted context.


### `create_app.jobs`

```python
create_app.jobs(ctx=Depends(identity))
```

Return visible upload jobs in newest-first order.


### `create_app.job`

```python
create_app.job(identifier: UUID, ctx=Depends(identity))
```

Return one visible upload job by UUID, or not_found.


### `create_app.work`

```python
create_app.work(identifier)
```

Open a fresh worker connection and process one durable upload job; commit through the connection context.


### `create_app.upload`

```python
create_app.upload(background: BackgroundTasks, metadata: str=Form(...), file: UploadFile=File(...), ctx=Depends(identity))
```

Validate multipart metadata/file, override external-use permission, persist the upload, schedule processing, and return its job.


### `create_app.find`

```python
create_app.find(data: SearchInput, ctx=Depends(identity))
```

Accept SearchInput and return ranked evidence or an evidence gap through the data service.


## backend/data/__init__.py

[Open source](../../backend/data/__init__.py)

Jonathan's PostgreSQL data subsystem; Week 1 uses fictional fixtures only.

No named functions/classes. Package marker or module-level definitions only.


## backend/data/cli.py

[Open source](../../backend/data/cli.py)

Run with python -m backend.data.cli from the repository root.


### `main`

```python
main() -> int
```

Parse migrate/seed/lookup subcommands, print JSON, and return the documented exit code.


## backend/data/db.py

[Open source](../../backend/data/db.py)

Local connection configuration and transactional, checksummed migrations.


### `connect`

```python
connect(database: str | None=None, *, autocommit: bool=False)
```

Read local database configuration and return a psycopg connection using dictionary rows; reject an unset/placeholder password.


Implementation note: Environment values override the ignored local .env; never print secrets.


### `migrate`

```python
migrate(conn) -> list[str]
```

Apply unapplied SQL files transactionally and return filenames; reject changed historical checksums.


Implementation note: Apply new SQL files once; reject edits to already applied migrations.


## backend/data/export_contracts.py

[Open source](../../backend/data/export_contracts.py)

Regenerate the proposed repository schemas and examples without a database.


### `contract_files`

```python
contract_files() -> dict
```

Return v1 JSON Schema/example artifacts as a filename-to-content dictionary; no database required.


## backend/data/export_week2_contracts.py

[Open source](../../backend/data/export_week2_contracts.py)

Export version 2 input schemas and the local API's OpenAPI contract.


### `artifacts`

```python
artifacts()
```

Return v2 input schemas, OpenAPI, and assignment example as a filename-to-content dictionary.


### `main`

```python
main()
```

Write generated v2 contract artifacts under contracts/data/v2.


## backend/data/importer.py

[Open source](../../backend/data/importer.py)

CSV staging, exact money, conservative identity matching, and revision history.


### `clean_row`

```python
clean_row(conn, row, source)
```

Normalize and validate a CSV row against known entities; return (source-scoped identity key, normalized record, fallback-used flag).


### `import_csv`

```python
import_csv(conn, raw: bytes, manifest: dict)
```

Accept raw CSV and manifest; stage/import/revise payments with audit history; return import ID, inserted/updated/unchanged counts and rejected rows.


### `spending`

```python
spending(conn, *, department_id, start, end, budget, source_key, currency='USD')
```

Accept explicit department/date/source/currency and matching budget; return scoped decimal-string totals and consulting share or raise ValueError.


Implementation note: Scope payments AND caller-supplied budget to the same inclusive date range.  Budget is an explicit fixture object with its own scope; mismatches fail. source_key selects one export population, preventing Week 1 fixture overlap.


## backend/data/ingestion.py

[Open source](../../backend/data/ingestion.py)

Durable PDF intake; page-bounded chunks and immutable evidence versions.


### `digest`

```python
digest(content)
```

Accept bytes and return their hexadecimal SHA-256 digest.


### `submit_pdf`

```python
submit_pdf(conn, content: bytes, metadata: DocumentInput, context, max_bytes=10 * 1024 * 1024)
```

Accept connection, PDF bytes, metadata, and access context; enforce size/signature/ownership, persist a pending job, and return job UUID.


### `extract_chunks`

```python
extract_chunks(content)
```

Accept PDF bytes; return (one-based page number, text) tuples or raise a coded extraction error.


### `process_job`

```python
process_job(conn, job_id)
```

Accept a durable job UUID; commit processing then ready/failed state, writing immutable evidence when successful; return terminal state.


Implementation note: Caller commits submission first. Lock each document to serialize versions.  Processing and ready are committed separately by the worker connection. An interrupted processing job can be explicitly resumed with the same ID.


## backend/data/models.py

[Open source](../../backend/data/models.py)

Proposed Week 1 repository contract, separate from the existing engine schema.


### `Contract` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `AccessContext` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `Vendor` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `Department` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `Engagement` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `EngagementFound` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `EngagementNotFound` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


## backend/data/repository.py

[Open source](../../backend/data/repository.py)

The data boundary used by the API and engine, rather than duplicated SQL.


### `DataRepository` class

Bases: `object`. Groups the fields or methods listed in this reference.


### `DataRepository.__init__`

```python
DataRepository.__init__(self, connection)
```

Initialize DataRepository with the supplied dependencies/state; constructor returns no value.


### `DataRepository.get_engagement`

```python
DataRepository.get_engagement(self, engagement_id: UUID | str, access_context: AccessContext) -> EngagementResult
```

Accept UUID and trusted access context; return EngagementFound with nested vendor/department or EngagementNotFound.


Implementation note: Return permitted engagement with vendor/department, or typed not_found.  Missing and forbidden IDs deliberately share the same result. The API must derive access_context from authentication; this method cannot do so. Invalid UUID strings raise ValueError at this internal boundary.


## backend/data/search.py

[Open source](../../backend/data/search.py)

Measured keyword baseline; all eligibility filters run before ranking.


### `search`

```python
search(conn, request: SearchInput, context)
```

Accept SearchInput/context; filter and rank chunks, insert search audit record, return search_id/result_type/chunks.


## backend/data/seed.py

[Open source](../../backend/data/seed.py)

Insert the fixed Week 1 fixture atomically, with no duplicate or silent updates.


### `load_fixture`

```python
load_fixture() -> dict
```

Read and return the committed Week 1 fixture dictionary.


### `seed`

```python
seed(conn) -> dict[str, int]
```

Insert fixture records transactionally; return per-table inserted counts, reject conflicting existing values, and preserve stable IDs.


## backend/data/testing.py

[Open source](../../backend/data/testing.py)

Disposable databases shared by the Week 1 validator and integration tests.


### `empty_test_database`

```python
empty_test_database()
```

Yield a connection to a newly created random test database and drop that database on exit.


Implementation note: Create a fresh random database, never reset a supplied database name.  This requires CREATEDB on the local development role. Cleanup only drops the database successfully created by this invocation, including on test failure.


## backend/data/validate.py

[Open source](../../backend/data/validate.py)

One-command Week 1 demonstration against a newly created PostgreSQL database.


### `validate_database`

```python
validate_database(conn, checks: list[dict]) -> dict
```

Exercise Week 1 database acceptance checks; append check outcomes and return totals/lookup evidence.


Implementation note: Run exact checks; raise on the first mismatch and retain failed evidence.


### `validate_database.check`

```python
validate_database.check(name, actual, expected)
```

Append an actual-versus-expected acceptance check and fail if values differ.


### `validate_database.counts`

```python
validate_database.counts()
```

Query the seeded core table row counts for acceptance comparison.


### `source_fingerprint`

```python
source_fingerprint() -> str
```

Return SHA-256 over ordered data Python files, migrations, Week 1 fixture, and dependency lock.


### `main`

```python
main() -> int
```

Run disposable-database acceptance checks, write a reproducible validation record, and return success/failure exit code.


## backend/data/week2_cli.py

[Open source](../../backend/data/week2_cli.py)

Import a CSV plus source manifest into the configured local database.


### `main`

```python
main()
```

Read CSV/manifest arguments, migrate/import into configured DB, write/print results, return 2 for rejected rows or 0.


## backend/data/week2_demo.py

[Open source](../../backend/data/week2_demo.py)

Reproducible Week 2 import, persistence and retrieval baseline in a fresh DB.


### `run`

```python
run()
```

Run controlled CSV/PDF/workspace/retrieval scenarios in a disposable database; return spending, baseline, and deterministic-check evidence.


### `main`

```python
main()
```

Run the disposable Week 2 demo, attach provenance, and write/print its result.


## backend/data/week2_models.py

[Open source](../../backend/data/week2_models.py)

Strict input contracts shared by the data service and HTTP API.


### `AssignmentInput` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `AssignmentInput.nonblank`

```python
AssignmentInput.nonblank(cls, value)
```

Trim the decorated input fields and reject whitespace-only strings.


### `DocumentInput` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


### `DocumentInput.nonblank`

```python
DocumentInput.nonblank(cls, value)
```

Trim the decorated input fields and reject whitespace-only strings.


### `DocumentInput.unknown_is_not_approved`

```python
DocumentInput.unknown_is_not_approved(self)
```

Reject unknown-access documents approved for external use; otherwise return the validated model.


### `SearchInput` class

Bases: `Contract`. Groups the fields or methods listed in this reference.


## backend/data/workspace.py

[Open source](../../backend/data/workspace.py)

Persist assignments and expose only ready, authorized document versions.


### `DataError` class

Bases: `ValueError`. Groups the fields or methods listed in this reference.


### `DataError.__init__`

```python
DataError.__init__(self, code, status=400)
```

Initialize DataError with the supplied dependencies/state; constructor returns no value.


### `require_department`

```python
require_department(context, department_id)
```

Return normally if the department is allowed; otherwise raise not_found (404).


### `list_documents`

```python
list_documents(conn, context)
```

Query and return ready version dictionaries in allowed departments with known access status.


### `save_assignment`

```python
save_assignment(conn, data: AssignmentInput, context)
```

Validate department/source access; insert assignment and source links; return saved input plus ID/version/timestamp.


### `get_assignment`

```python
get_assignment(conn, identifier, context)
```

Read an owner-and-department-scoped assignment; return its payload plus server fields or raise not_found.


### `list_jobs`

```python
list_jobs(conn, context)
```

Return visible job summaries with status, IDs, title, byte count, and error.


### `get_job`

```python
get_job(conn, job_id, context)
```

Select one job from visible summaries; return it or raise not_found.


## backend/engine/__init__.py

[Open source](../../backend/engine/__init__.py)

No named functions/classes. Package marker or module-level definitions only.


## backend/engine/adapters.py

[Open source](../../backend/engine/adapters.py)


### `ModelAdapter` class

Bases: `Protocol`. Groups the fields or methods listed in this reference.


### `ModelAdapter.generate`

```python
ModelAdapter.generate(self, assignment: Assignment, evidence: list[EvidenceChunk]) -> tuple[dict, UsageRecord]
```

Adapter interface/test implementation: accept assignment/evidence and return (report dictionary, UsageRecord).


### `MockModelAdapter` class

Bases: `object`. Deterministic Week 1 adapter. No API key or network call is required.


### `MockModelAdapter.__init__`

```python
MockModelAdapter.__init__(self, response_path: str | Path)
```

Initialize MockModelAdapter with the supplied dependencies/state; constructor returns no value.


### `MockModelAdapter.generate`

```python
MockModelAdapter.generate(self, assignment: Assignment, evidence: list[EvidenceChunk]) -> tuple[dict, UsageRecord]
```

Read saved report JSON, replace assignment ID, increment call_count; return (report dictionary, mock UsageRecord). No network call.


## backend/engine/models.py

[Open source](../../backend/engine/models.py)


### `Assignment` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `Assignment.problem_must_not_be_blank`

```python
Assignment.problem_must_not_be_blank(cls, value: str) -> str
```

Trim problem text and reject whitespace-only input.


### `EvidenceChunk` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `Citation` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `ReportSection` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `Report` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `Report.validate_citation_references`

```python
Report.validate_citation_references(self)
```

Ensure each report section citation ID exists in the report citation list; return self or raise ValueError.


### `ScopeCheckResult` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `UsageRecord` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `EngineSuccess` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `EngineNeedsInput` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


### `EngineFailure` class

Bases: `BaseModel`. Groups the fields or methods listed in this reference.


## backend/engine/pipeline.py

[Open source](../../backend/engine/pipeline.py)


### `validate_assignment`

```python
validate_assignment(data: dict | Assignment) -> Assignment
```

Return a validated engine Assignment from a dictionary or pass through an Assignment; invalid values raise ValidationError.


### `retrieve_evidence`

```python
retrieve_evidence(assignment: Assignment)
```

Return fixed fixture evidence for the assignment; used when no repository is injected.


### `validate_report`

```python
validate_report(raw_report: dict, valid_evidence_ids: set[str]) -> Report
```

Parse Report; verify every citation targets a retrieved chunk; return the validated report or raise a validation/value error.


### `run_engine`

```python
run_engine(data: dict | Assignment, model_client: ModelAdapter, evidence_repository=None) -> EngineResult
```

Validate, clarify, retrieve, invoke adapter, and validate report; return typed report/needs_input/error result. See workflow guide for caught errors.


## backend/engine/repository.py

[Open source](../../backend/engine/repository.py)


### `get_fixture_evidence`

```python
get_fixture_evidence(assignment: Assignment) -> list[EvidenceChunk]
```

Return a copy of the two fixed fixture chunks. The main-branch fixture repository ignores assignment selection and department; use the database adapter for scoped retrieval.


## backend/engine/retrieval.py

[Open source](../../backend/engine/retrieval.py)

Real evidence adapter: explicit filters, deduplication, bounded text context.


### `DataEvidenceRepository` class

Bases: `object`. Groups the fields or methods listed in this reference.


### `DataEvidenceRepository.__init__`

```python
DataEvidenceRepository.__init__(self, connection, context, max_chars=6000)
```

Initialize DataEvidenceRepository with the supplied dependencies/state; constructor returns no value.


### `DataEvidenceRepository.__call__`

```python
DataEvidenceRepository.__call__(self, assignment)
```

Retrieve eligible database evidence for an assignment; enforce department scope, hash deduplication and whole-chunk character cap; retain last_result and return EvidenceChunk objects.


## backend/engine/runner.py

[Open source](../../backend/engine/runner.py)


### `main`

```python
main() -> int
```

Read assignment and saved-response paths, run the mock engine, write/print JSON and return 0 or 1.


## backend/engine/scope.py

[Open source](../../backend/engine/scope.py)


### `check_scope`

```python
check_scope(assignment: Assignment) -> ScopeCheckResult
```

Return ready or needs_input with questions and missing fields, including constraints for an underspecified RFQ.


## scripts/create_week2_fixtures.py

[Open source](../../scripts/create_week2_fixtures.py)

Regenerate the deterministic fictional PDF (no City records).

No named functions/classes. Executes its script workflow at module level; inspect the source before importing it.


## scripts/record_week1_evidence.py

[Open source](../../scripts/record_week1_evidence.py)

Record actual Week 1 checks; run with .venv/bin/python from any directory.


### `main`

```python
main() -> int
```

Run the Week 1 evidence-recording commands and save their outputs and run manifest.


## scripts/resume_uploads.py

[Open source](../../scripts/resume_uploads.py)

After stopping the API, resume durable pending/interrupted PDF jobs.

No named functions/classes. Executes its script workflow at module level; inspect the source before importing it.


## scripts/serve_week2.py

[Open source](../../scripts/serve_week2.py)

Start the local fixture demo. Prints a new short-lived local access token.

No named functions/classes. Executes its script workflow at module level; inspect the source before importing it.


## scripts/setup_local.py

[Open source](../../scripts/setup_local.py)

Create a local Python environment, start PostgreSQL, migrate and seed.

Run from any directory with Python 3.12 or 3.13. Docker Desktop must be running.
Existing .env files and database volumes are preserved.


### `run`

```python
run(*args)
```

Execute a subprocess in the repository root with check=True; raise on failure.


### `main`

```python
main()
```

Verify runtime/Docker, create .env and virtual environment if needed, install lockfile, start PostgreSQL, migrate and seed.


## scripts/test_week2_browser.py

[Open source](../../scripts/test_week2_browser.py)

Run real-browser checks against a disposable, freshly migrated database.


### `main`

```python
main()
```

Create/migrate/seed a disposable database and run npm browser tests with isolated configuration; exit with their status.


## tests/conftest.py

[Open source](../../tests/conftest.py)


### `pytest_addoption`

```python
pytest_addoption(parser)
```

Register --run-data so database integration tests run only when explicitly requested.


## tests/test_data.py

[Open source](../../tests/test_data.py)

Real PostgreSQL checks. Run: python -m pytest --run-data -q


### `empty_db`

```python
empty_db(request)
```

Test helper/fixture: empty db. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `seeded_db`

```python
seeded_db(empty_db)
```

Test helper/fixture: seeded db. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `insert_payment`

```python
insert_payment(conn, *, vendor=None, engagement='30000000-0000-4000-8000-000000000001', amount='1.00')
```

Test helper/fixture: insert payment. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `test_full_week1_acceptance_in_empty_database`

```python
test_full_week1_acceptance_in_empty_database(empty_db)
```

Regression check: full week1 acceptance in empty database. Uses assertions; returns no application result.


### `test_seed_keeps_ids_and_amounts_identical`

```python
test_seed_keeps_ids_and_amounts_identical(seeded_db)
```

Regression check: seed keeps ids and amounts identical. Uses assertions; returns no application result.


### `test_seed_conflict_rolls_back_partial_insert`

```python
test_seed_conflict_rolls_back_partial_insert(seeded_db, monkeypatch)
```

Regression check: seed conflict rolls back partial insert. Uses assertions; returns no application result.


### `test_migration_checksum_detects_changed_history`

```python
test_migration_checksum_detects_changed_history(seeded_db, monkeypatch, tmp_path)
```

Regression check: migration checksum detects changed history. Uses assertions; returns no application result.


### `test_failed_migration_rolls_back_schema`

```python
test_failed_migration_rolls_back_schema(empty_db, monkeypatch, tmp_path)
```

Regression check: failed migration rolls back schema. Uses assertions; returns no application result.


### `test_unknown_vendor_rejected`

```python
test_unknown_vendor_rejected(seeded_db)
```

Regression check: unknown vendor rejected. Uses assertions; returns no application result.


### `test_payment_cannot_disagree_with_engagement_vendor`

```python
test_payment_cannot_disagree_with_engagement_vendor(seeded_db)
```

Regression check: payment cannot disagree with engagement vendor. Uses assertions; returns no application result.


### `test_unknown_engagement_can_remain_null`

```python
test_unknown_engagement_can_remain_null(seeded_db)
```

Regression check: unknown engagement can remain null. Uses assertions; returns no application result.


### `test_refunds_use_exact_decimal_without_float`

```python
test_refunds_use_exact_decimal_without_float(seeded_db)
```

Regression check: refunds use exact decimal without float. Uses assertions; returns no application result.


### `test_nan_money_is_rejected`

```python
test_nan_money_is_rejected(seeded_db)
```

Regression check: nan money is rejected. Uses assertions; returns no application result.


### `test_other_department_context_cannot_lookup`

```python
test_other_department_context_cannot_lookup(seeded_db)
```

Regression check: other department context cannot lookup. Uses assertions; returns no application result.


### `test_invalid_uuid_cannot_be_used_as_sql`

```python
test_invalid_uuid_cannot_be_used_as_sql(seeded_db)
```

Regression check: invalid uuid cannot be used as sql. Uses assertions; returns no application result.


### `insert_document`

```python
insert_document(conn)
```

Test helper/fixture: insert document. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `test_document_provenance_defaults_deny_external_use`

```python
test_document_provenance_defaults_deny_external_use(seeded_db)
```

Regression check: document provenance defaults deny external use. Uses assertions; returns no application result.


### `test_chunk_requires_existing_document_version`

```python
test_chunk_requires_existing_document_version(seeded_db)
```

Regression check: chunk requires existing document version. Uses assertions; returns no application result.


### `test_old_evidence_cannot_be_overwritten`

```python
test_old_evidence_cannot_be_overwritten(seeded_db)
```

Regression check: old evidence cannot be overwritten. Uses assertions; returns no application result.


## tests/test_data_contracts.py

[Open source](../../tests/test_data_contracts.py)


### `test_published_contracts_match_models_and_fixture`

```python
test_published_contracts_match_models_and_fixture()
```

Regression check: published contracts match models and fixture. Uses assertions; returns no application result.


## tests/test_engine.py

[Open source](../../tests/test_engine.py)


### `load`

```python
load(name: str)
```

Test helper/fixture: load. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `test_complete_assignment_returns_valid_draft_report`

```python
test_complete_assignment_returns_valid_draft_report()
```

Regression check: complete assignment returns valid draft report. Uses assertions; returns no application result.


### `test_invalid_model_output_returns_typed_error`

```python
test_invalid_model_output_returns_typed_error()
```

Regression check: invalid model output returns typed error. Uses assertions; returns no application result.


### `test_rfq_only_needs_input_before_model_call`

```python
test_rfq_only_needs_input_before_model_call()
```

Regression check: rfq only needs input before model call. Uses assertions; returns no application result.


## tests/test_week2.py

[Open source](../../tests/test_week2.py)

Week 2 acceptance and regression checks using disposable PostgreSQL databases.


### `database`

```python
database(request)
```

Test helper/fixture: database. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `metadata`

```python
metadata(**changes)
```

Test helper/fixture: metadata. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `ingest`

```python
ingest(conn, content=PDF, **changes)
```

Test helper/fixture: ingest. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `assignment`

```python
assignment(**changes)
```

Test helper/fixture: assignment. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `test_money_repeat_and_scope`

```python
test_money_repeat_and_scope(database)
```

Regression check: money repeat and scope. Uses assertions; returns no application result.


### `test_rejections_and_traceable_correction`

```python
test_rejections_and_traceable_correction(database)
```

Regression check: rejections and traceable correction. Uses assertions; returns no application result.


### `test_collision_and_legitimate_equal_payments`

```python
test_collision_and_legitimate_equal_payments(database)
```

Regression check: collision and legitimate equal payments. Uses assertions; returns no application result.


### `test_invalid_money`

```python
test_invalid_money(database, replacement)
```

Regression check: invalid money. Uses assertions; returns no application result.


### `test_versions_and_page_search`

```python
test_versions_and_page_search(database)
```

Regression check: versions and page search. Uses assertions; returns no application result.


### `test_failed_documents_have_no_evidence`

```python
test_failed_documents_have_no_evidence(database)
```

Regression check: failed documents have no evidence. Uses assertions; returns no application result.


### `test_assignments_and_authorization`

```python
test_assignments_and_authorization(database)
```

Regression check: assignments and authorization. Uses assertions; returns no application result.


### `CaptureModel` class

Bases: `object`. Groups the fields or methods listed in this reference.


### `CaptureModel.generate`

```python
CaptureModel.generate(self, assignment, evidence)
```

Adapter interface/test implementation: accept assignment/evidence and return (report dictionary, UsageRecord).


### `test_engine_evidence_permissions_and_gap`

```python
test_engine_evidence_permissions_and_gap(database)
```

Regression check: engine evidence permissions and gap. Uses assertions; returns no application result.


### `client_for`

```python
client_for(database, **options)
```

Test helper/fixture: client for. Creates or loads inputs/dependencies used by the surrounding regression tests; see linked source for fixture lifecycle.


### `test_api_persistence_upload_and_failures`

```python
test_api_persistence_upload_and_failures(database)
```

Regression check: api persistence upload and failures. Uses assertions; returns no application result.


### `test_api_cannot_self_approve_model_use`

```python
test_api_cannot_self_approve_model_use(database)
```

Regression check: api cannot self approve model use. Uses assertions; returns no application result.


### `test_api_refuses_nonlocal_configuration`

```python
test_api_refuses_nonlocal_configuration()
```

Regression check: api refuses nonlocal configuration. Uses assertions; returns no application result.


### `test_exported_week2_contracts_match`

```python
test_exported_week2_contracts_match()
```

Regression check: exported week2 contracts match. Uses assertions; returns no application result.


### `test_interrupted_job_can_resume_and_unknown_access_is_hidden`

```python
test_interrupted_job_can_resume_and_unknown_access_is_hidden(database)
```

Regression check: interrupted job can resume and unknown access is hidden. Uses assertions; returns no application result.


### `test_chunk_budget_and_deduplication`

```python
test_chunk_budget_and_deduplication(database)
```

Regression check: chunk budget and deduplication. Uses assertions; returns no application result.


### `test_invalid_shared_ids_return_structured_engine_error`

```python
test_invalid_shared_ids_return_structured_engine_error(database)
```

Regression check: invalid shared ids return structured engine error. Uses assertions; returns no application result.


### `test_unapproved_readable_document_can_be_read_but_not_sent_externally`

```python
test_unapproved_readable_document_can_be_read_but_not_sent_externally(database)
```

Regression check: unapproved readable document can be read but not sent externally. Uses assertions; returns no application result.


### `test_changed_pdf_preserves_old_chunks`

```python
test_changed_pdf_preserves_old_chunks(database)
```

Regression check: changed pdf preserves old chunks. Uses assertions; returns no application result.


### `test_same_job_concurrent_workers_create_one_version`

```python
test_same_job_concurrent_workers_create_one_version(database)
```

Regression check: same job concurrent workers create one version. Uses assertions; returns no application result.


### `test_same_job_concurrent_workers_create_one_version.work`

```python
test_same_job_concurrent_workers_create_one_version.work()
```

Open a fresh worker connection and process one durable upload job; commit through the connection context.


### `test_engine_respects_assignment_department_even_if_actor_can_read_both`

```python
test_engine_respects_assignment_department_even_if_actor_can_read_both(database)
```

Regression check: engine respects assignment department even if actor can read both. Uses assertions; returns no application result.


## Frontend functions — apps/web/src/main.tsx

[Open source](../../apps/web/src/main.tsx)

- `App()`: React component; owns token, connection, assignment, documents/jobs, messages, busy/uploading flags, file, query, chunks, and search state; returns workspace JSX.
- `api(path, options = {})`: adds `/api/v1` and bearer header, parses response JSON, throws a friendly mapped error on non-2xx, returns response body otherwise.
- `refresh()`: fetches documents and upload jobs concurrently and updates both state arrays; resolves without an application result.
- `connect()`: refreshes data, stores token, marks connection active, and restores the last saved assignment ID when available; displays errors in state.
- `upload(event)`: prevents form submission, creates multipart PDF metadata/file, posts it, refreshes lists, and updates progress/error/notice state.
- `save(event)`: sends a whitelist of assignment input fields, stores the new assignment ID, replaces form state with the saved response, and displays feedback.
- `find(event)`: posts query and selected versions (empty selection becomes null), stores chunks and searched state, and displays errors.
- Effect callback: starts a two-second document/job refresh interval when connected; cleanup clears it. Re-runs when connection or token changes.
- Inline change/click callbacks: update form fields, file/query/token state, and selected version IDs. Changing the token disconnects the UI. No additional standalone frontend business functions exist on this snapshot.
- `createRoot(...).render(...)`: mounts `App` into the root element at module load.

Frontend types: `Document` contains version ID/title/version/external permission;
`Job` contains job ID/title/status/error/size; `Chunk` contains ID/title/locator/text;
`Assignment` contains editable assignment fields and optional saved ID. These are
UI projections, not full API response schemas. Vite and Playwright configuration
files export configuration objects; the browser tests use anonymous test/route
callbacks rather than additional named application functions.

## SQL function

[`reject_evidence_mutation()`](../../backend/data/migrations/001_initial.sql)
returns the SQL `trigger` type but always raises an exception (SQLSTATE `23514`)
when an update/delete is attempted on `document_versions` or `chunks`. Two
BEFORE triggers attach it to those tables. Migration 002 adds no SQL functions.
