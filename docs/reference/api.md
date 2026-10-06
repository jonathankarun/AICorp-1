# HTTP API reference

[Handbook home](README.md) · [Input models](contracts.md)

Implementation: [`backend/api/app.py`](../../backend/api/app.py).
Base URL for the launcher: `http://127.0.0.1:8000`.
Interactive documentation: `/docs` and `/redoc`; machine-readable schema:
`/openapi.json`. The committed [OpenAPI snapshot](../../contracts/data/v2/openapi.json)
is generated from the app. Several response shapes are returned as dictionaries,
so this guide also documents fields not fully described by OpenAPI.

## Authentication and application configuration

All endpoints below except health require `Authorization: Bearer <local token>`.
The server must have `AICORP_LOCAL_DEMO=1` and a token of at least 16 characters;
otherwise startup fails. Allowed hostnames are `localhost`, `127.0.0.1`, and
`testserver`. The default actor is `50000000-0000-4000-8000-000000000001`, with
access to department `10000000-0000-4000-8000-000000000001`.

`create_app()` allows tests to inject a connection factory, trusted context,
token, local-mode setting, and upload limit. These are server-side configuration,
not fields a browser can set.

## GET /api/v1/health

No body or authentication. HTTP 200:

```json
{"status":"ok","mode":"local-fixture-demo"}
```

This only reports API liveness, not database readiness.

## POST /api/v1/assignments

JSON body: `AssignmentInput` from [Inputs and outputs](contracts.md).
HTTP 201: the saved input fields plus `assignment_id` (UUID),
`schema_version: "2.0"`, and `created_at` (timestamp).
Creates a new record on every call. No idempotency key or update semantics.

```bash
# Set AICORP_DEMO_TOKEN in your shell to the token printed by the launcher.
curl -sS http://127.0.0.1:8000/api/v1/assignments \
  -H "Authorization: Bearer $AICORP_DEMO_TOKEN" \
  -H 'Content-Type: application/json' \
  --data-binary @contracts/data/v2/assignment.example.json
```

An inaccessible department produces 404. A selected source that is not ready or
not visible produces 422 `source_not_ready_or_not_allowed`.

## GET /api/v1/assignments/{identifier}

`identifier` must be a UUID. No body. HTTP 200: the same saved-assignment shape.
Requires both actor ownership and allowed-department membership. Missing and
inaccessible records both produce 404 `not_found`.

## GET /api/v1/documents

No body. HTTP 200: an array of ready document-version objects. Each contains:
`document_version_id`, `document_id`, `version`, nullable `engagement_id`, `title`,
nullable `issuer`, nullable `published_on`, `source_uri`, `content_hash`,
`extraction_version`, `access_status`, `external_model_allowed`, and `department_id`.
Dates are JSON date strings and UUIDs are strings. Ordered by title, then newest
version first. Multiple versions of one document may appear. Unknown-access,
unready, and other-department evidence is hidden. A readable source can still be
ineligible for outbound-model use.

## POST /api/v1/documents

Multipart body with **both** fields:

- `file`: PDF bytes, MIME `application/pdf` or `application/octet-stream`.
- `metadata`: a string containing `DocumentInput` JSON (not a nested JSON body).

HTTP 202 returns the upload-job object described below. Processing is scheduled
after submission; acceptance does not mean the source is ready.

```bash
curl -sS http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $AICORP_DEMO_TOKEN" \
  -F 'file=@tests/fixtures/week2/engagement.pdf;type=application/pdf' \
  -F 'metadata={"department_id":"10000000-0000-4000-8000-000000000001","title":"Fictional engagement","source_uri":"fixture://engagement.pdf","access_status":"public"}'
```

The server overrides `external_model_allowed`: only an exact byte match to the
bundled fictional PDF, with public access, is allowlisted. Declaring an arbitrary
file public or sending `external_model_allowed: true` does not grant approval.

## GET /api/v1/uploads and GET /api/v1/uploads/{identifier}

No body. HTTP 200 returns respectively an array of jobs (newest first) or a
single job. Individual identifiers must be UUIDs. Fields:

- `job_id`, `document_id`: UUID strings.
- `status`: `pending`, `processing`, `ready`, or `failed`.
- `document_version_id`: UUID string once ready; otherwise null.
- `error_code`: failure reason or null.
- `title`: submitted metadata title.
- `size_bytes`: stored upload size.

Visibility follows department membership. Missing/inaccessible individual jobs
return 404. Raw file bytes and the full internal job metadata are not returned.

## POST /api/v1/search

JSON body: `SearchInput`. HTTP 200:

```json
{"search_id":"<UUID>","result_type":"evidence_gap","chunks":[]}
```

With matches, `result_type` is `evidence`; each chunk contains `chunk_id`,
`document_version_id`, `text`, `page_number`, `content_hash`, `title`, `source_uri`,
`access_status`, `external_model_allowed`, `score`, and `locator` such as `page 1`.

```bash
curl -sS http://127.0.0.1:8000/api/v1/search \
  -H "Authorization: Bearer $AICORP_DEMO_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"query":"permit intake","selected_document_version_ids":null,"limit":5,"for_external_model":true}'
```

`for_external_model: false` permits readable, unapproved evidence for internal
search; it does not bypass department membership, readiness, or unknown-access
filtering. A zero-match search is a successful HTTP response, not HTTP 404.

## Error responses

Domain errors use `{"error":{"code":"..."}}`:

- 401 `unauthorized`: missing/incorrect token or disabled local mode.
- 404 `not_found`: missing record or hidden by authorization.
- 413 `file_too_large`: more than the configured byte limit.
- 415 `pdf_required`: unacceptable MIME type or missing PDF signature.
- 422 `invalid_document_metadata`: metadata fails the document model.
- 422 `source_not_ready_or_not_allowed`: an assignment selected an unavailable source.
- 503 `database_unavailable`: a caught PostgreSQL driver error.

FastAPI request-validation failures produce HTTP 422 with
`{"error":{"code":"invalid_request","fields":["body.problem"]}}`;
field paths vary with the failure. Middleware/framework errors (for example an
invalid Host header or nonexistent route) need not use the domain-error envelope.

Extraction failures occur **after HTTP 202** and appear in the job's `error_code`:
`pdf_encrypted_or_too_many_pages`, `empty_or_scanned_page`,
`extracted_text_too_large`, or `unreadable_pdf`. Poll the job to see them.

## Routes that are not present on main

There is no assignment update/delete/list endpoint, CSV-import HTTP route,
spending HTTP route, report persistence endpoint, or consultation endpoint.
CSV and spending functionality are Python/CLI interfaces. The separate
[`yasha-week2` consultation route](branches.md) is not part of this main snapshot.
