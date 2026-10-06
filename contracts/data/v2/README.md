# Week 2 data/API contract

Implemented locally; awaiting team adoption. Week 1 engagement lookup remains
unchanged. Version 2 adds assignment input, document intake/status, and search.
See `openapi.json` or the running API's `/docs` for HTTP input definitions.

## ID and ownership rules

Real IDs are UUIDs serialized as JSON strings. Source labels such as
`dept-fixture-001` remain source keys, not UUIDs. The UI uses the seeded department
UUID. Jai's legacy Week 1 mocks still work; pass `DataEvidenceRepository` to the
engine for real UUID-backed evidence. No global fixture-ID rewrite is required.

The HTTP adapter derives a fixed local test `AccessContext` after validating a
Bearer token. Clients cannot submit `created_by`, actor identity, or department
permissions. Assignment reads require both ownership and department access.
Document reads/search require department access. Document updates require the
original actor and department. Missing and forbidden resources use `not_found`.

## Calls

- `POST /api/v1/assignments`: strict `AssignmentInput`; returns 201 with ID,
  normalized fields, schema version, and creation time. Selected versions must
  be ready and readable. A save creates a new assignment; revision editing and
  request idempotency are future workflow features.
- `GET /api/v1/assignments/{uuid}`: read the saved assignment.
- `POST /api/v1/documents`: multipart `file` plus JSON-string `metadata` matching
  `DocumentInput`; returns 202 with job ID, document ID, title, size, status,
  optional version ID, and error code. The raw bytes are stored in PostgreSQL
  under generated IDs; the user filename is never a filesystem path.
- `GET /api/v1/uploads` and `/uploads/{uuid}`: processing state. Flow is pending
  → processing → ready or failed. Ready requires a committed immutable version.
- `GET /api/v1/documents`: only ready readable version records, with provenance,
  hash, access status, and outbound-model eligibility.
- `POST /api/v1/search`: query, version filters, limit (1–20), and
  `for_external_model` (default true). Returns search ID, `evidence` or
  `evidence_gap`, and chunks with ID, version ID, text, title, source URI,
  page number, locator, hash, eligibility, and keyword score.

Search filters are intersections: allowed departments AND readable/ready status
AND selected versions when supplied AND external approval when requested.
`selected_document_version_ids: null` searches all eligible sources; `[]` searches
none. The UI and engine map no user selection to null. Terms use OR matching with
English stemming; ordering is score descending then stable chunk ID. Scores are
keyword relevance scores, not confidence or truth probabilities.

The engine further restricts retrieval to the assignment's department within
the caller's memberships. The engine's adapter includes whole deduplicated chunks up to 6,000 characters
by default, with a 20-candidate search cap. It preserves page locators and checks
outbound eligibility again. No evidence produces `needs_input` with
`eligible_evidence` missing and zero model calls. Invalid UUID filters return a
structured engine error. Existing mock behavior remains the default for Week 1.

## Errors

Error JSON has `error.code`; validation may include field locations, never raw
input values or server paths. Key responses: 401 unauthorized, 404 missing/hidden,
413 upload too large, 415 unsupported content, 422 invalid input/selection, and
503 database unavailable. Corrupt PDFs that pass the PDF header check receive a
job that transitions to failed (`unreadable_pdf`). Blank/scanned pages produce
`empty_or_scanned_page`. The UI offers corrective guidance and preserves forms.

## CSV and financial scope

Exact headers are in `tests/fixtures/week2/payments.csv`. Values are trimmed;
known vendor/department source keys or unambiguous case-insensitive names match.
Unknown aliases are rejected for review. Dates use ISO YYYY-MM-DD. USD amounts
use exact decimals, support refunds, and reject nonfinite/sub-cent amounts.
Classification is consulting, operational, or unresolved with required rationale.

Identity is source namespace + transaction ID. Without a transaction ID, a
hash of vendor, department, date, amount, currency, and engagement forms a
conservative fallback. Duplicate identities within one file are quarantined,
including both colliding rows. Equal date/amount/vendor values with different
transaction IDs remain separate. A repeat import records an attempt and leaves
unchanged payments alone. Explicit-ID corrections record old/new revisions.
Fallback corrections or indistinguishable payments require human identity review.

The raw file and every staged row remain in the database. Import results include
inserted/updated/unchanged counts and a rejected-row report. An import never
silently deletes missing rows. A fresh Week 2 source namespace is separate from
the historical Week 1 fixture, so the financial query explicitly names its source
population; do not sum all demo payments and call that the Week 2 total.

Spending requires a matching department, inclusive date interval, currency, source
namespace, and positive budget. Budget values are explicit fixture inputs, not
inferred City appropriations. Only confirmed consulting enters the numerator;
unresolved spending is displayed separately.

## Immutable evidence and mutable state

`documents` owns the stable document identity and department/actor scope.
`ingestion_jobs` preserves original bytes and mutable state. `document_versions`
and `chunks` remain append-only. Re-uploading identical bytes/metadata for the
same document reuses a version; changed bytes or provenance create a new version.
Chunk IDs derive from version UUID plus ordinal. A per-document row lock prevents
concurrent workers allocating duplicate versions. Old selections/citations remain
valid. Public access status never implies external-model approval.
