# Inputs and outputs

[Handbook home](README.md) · [HTTP examples](api.md)

## How to read the model catalog

Each field below shows its actual Python type and default/validation declaration.
**Required** means callers must supply it; `None` means JSON null; `list[str]`
means an array of strings; `UUID` is a UUID string on the wire. `Literal[...]`
lists the only permitted values. `Field(default_factory=list)` creates an empty
list per request. Length limits are character counts for strings and item counts
for lists. Dates use ISO `YYYY-MM-DD`.

The data models inherit `Contract`, which forbids unknown fields and freezes
model instances. Engine models inherit Pydantic `BaseModel` with its default
configuration; they do not inherit those stricter data-contract settings.
HTTP AssignmentInput requires a UUID department and intended result. Engine
Assignment uses string IDs and permits missing information so the scope checker
can ask clarification questions. Do not interchange these schemas blindly.

### Validation beyond field declarations

- AssignmentInput trims/rejects blank problem and intended result; up to 50 selected versions.
- DocumentInput trims/rejects blank title and source URI; unknown access cannot be externally approved. HTTP upload overrides external approval with its allowlist policy.
- SearchInput accepts 1–2,000 query characters, limit 1–20 (default 5); it does not trim/reject whitespace separately. A punctuation/whitespace-only query can yield an evidence gap.
- Engine Assignment trims/rejects blank problem. Scope checks require intended result/department and RFQ constraints before generation.
- Report validates section citation IDs. The pipeline separately validates citations against retrieved evidence IDs.

## Complete model field catalog


### [backend/data/models.py](../../backend/data/models.py)


#### `Contract`

Shared model configuration; no declared payload fields.


#### `AccessContext`

- `actor_id` — `UUID`; **required**.
- `allowed_department_ids` — `tuple[UUID, ...]`; default/constraints: `()`.

#### `Vendor`

- `vendor_id` — `UUID`; **required**.
- `source_key` — `str`; **required**.
- `name` — `str`; **required**.
- `source_uri` — `str`; **required**.

#### `Department`

- `department_id` — `UUID`; **required**.
- `source_key` — `str`; **required**.
- `name` — `str`; **required**.
- `source_uri` — `str`; **required**.

#### `Engagement`

- `engagement_id` — `UUID`; **required**.
- `source_key` — `str`; **required**.
- `title` — `str`; **required**.
- `source_uri` — `str`; **required**.
- `vendor` — `Vendor`; **required**.
- `department` — `Department`; **required**.

#### `EngagementFound`

- `result_type` — `Literal['engagement']`; default/constraints: `'engagement'`.
- `schema_version` — `Literal['1.0']`; default/constraints: `'1.0'`.
- `engagement` — `Engagement`; **required**.

#### `EngagementNotFound`

- `result_type` — `Literal['not_found']`; default/constraints: `'not_found'`.
- `schema_version` — `Literal['1.0']`; default/constraints: `'1.0'`.
- `engagement_id` — `UUID`; **required**.
- `code` — `Literal['engagement_not_found']`; default/constraints: `'engagement_not_found'`.
- `message` — `str`; default/constraints: `'Engagement not found or not accessible.'`.

### [backend/data/week2_models.py](../../backend/data/week2_models.py)


#### `AssignmentInput`

- `problem` — `str`; default/constraints: `Field(min_length=1, max_length=10000)`.
- `department_id` — `UUID`; **required**.
- `intended_result` — `str`; default/constraints: `Field(min_length=1, max_length=3000)`.
- `required_sections` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `audience` — `str | None`; default/constraints: `None`.
- `constraints` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `selected_document_version_ids` — `list[UUID]`; default/constraints: `Field(default_factory=list, max_length=50)`.
- `request_type` — `Literal['problem', 'RFP', 'RFQ']`; default/constraints: `'problem'`.

#### `DocumentInput`

- `department_id` — `UUID`; **required**.
- `title` — `str`; default/constraints: `Field(min_length=1, max_length=300)`.
- `source_uri` — `str`; default/constraints: `Field(min_length=1, max_length=1000)`.
- `issuer` — `str | None`; default/constraints: `None`.
- `published_on` — `date | None`; default/constraints: `None`.
- `access_status` — `Literal['public', 'restricted', 'unknown']`; default/constraints: `'unknown'`.
- `external_model_allowed` — `bool`; default/constraints: `False`.
- `document_id` — `UUID | None`; default/constraints: `None`.

#### `SearchInput`

- `query` — `str`; default/constraints: `Field(min_length=1, max_length=2000)`.
- `selected_document_version_ids` — `list[UUID] | None`; default/constraints: `Field(default=None, max_length=50)`.
- `limit` — `int`; default/constraints: `Field(default=5, ge=1, le=20)`.
- `for_external_model` — `bool`; default/constraints: `True`.

### [backend/engine/models.py](../../backend/engine/models.py)


#### `Assignment`

- `assignment_id` — `str`; **required**.
- `schema_version` — `str`; default/constraints: `'1.0'`.
- `problem` — `str`; **required**.
- `department_id` — `str | None`; default/constraints: `None`.
- `intended_result` — `str | None`; default/constraints: `None`.
- `required_sections` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `audience` — `str | None`; default/constraints: `None`.
- `constraints` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `selected_document_version_ids` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `request_type` — `Literal['problem', 'RFP', 'RFQ']`; default/constraints: `'problem'`.

#### `EvidenceChunk`

- `chunk_id` — `str`; **required**.
- `document_version_id` — `str`; **required**.
- `title` — `str`; **required**.
- `source_uri` — `str`; **required**.
- `locator` — `str`; **required**.
- `text` — `str`; **required**.
- `access_scope` — `str`; default/constraints: `'fixture'`.
- `external_model_allowed` — `bool`; default/constraints: `True`.

#### `Citation`

- `citation_id` — `str`; **required**.
- `evidence_chunk_id` — `str`; **required**.

#### `ReportSection`

- `name` — `str`; **required**.
- `content` — `str`; **required**.
- `citation_ids` — `list[str]`; default/constraints: `Field(default_factory=list)`.

#### `Report`

- `report_id` — `str`; **required**.
- `assignment_id` — `str`; **required**.
- `version` — `int`; default/constraints: `1`.
- `status` — `Literal['draft', 'reviewed', 'approved']`; default/constraints: `'draft'`.
- `sections` — `list[ReportSection]`; **required**.
- `citations` — `list[Citation]`; **required**.
- `assumptions` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `missing_information` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `expert_review_needed` — `list[str]`; default/constraints: `Field(default_factory=list)`.

#### `ScopeCheckResult`

- `status` — `Literal['ready', 'needs_input']`; **required**.
- `questions` — `list[str]`; default/constraints: `Field(default_factory=list)`.
- `missing_fields` — `list[str]`; default/constraints: `Field(default_factory=list)`.

#### `UsageRecord`

- `provider` — `str`; **required**.
- `model` — `str`; **required**.
- `prompt_version` — `str`; **required**.
- `input_units` — `int`; default/constraints: `0`.
- `output_units` — `int`; default/constraints: `0`.
- `mock` — `bool`; default/constraints: `True`.

#### `EngineSuccess`

- `result_type` — `Literal['report']`; default/constraints: `'report'`.
- `report` — `Report`; **required**.
- `usage` — `UsageRecord`; **required**.

#### `EngineNeedsInput`

- `result_type` — `Literal['needs_input']`; default/constraints: `'needs_input'`.
- `assignment_id` — `str`; **required**.
- `questions` — `list[str]`; **required**.
- `missing_fields` — `list[str]`; **required**.
- `model_calls` — `int`; default/constraints: `0`.

#### `EngineFailure`

- `result_type` — `Literal['error']`; default/constraints: `'error'`.
- `code` — `str`; **required**.
- `message` — `str`; **required**.
- `retryable` — `bool`; default/constraints: `False`.

## Output shapes not declared as models

- Saved assignment: all normalized AssignmentInput fields, `assignment_id`, `schema_version: "2.0"`, `created_at`.
- Upload summary: `job_id`, `document_id`, `status`, `document_version_id`, `error_code`, `title`, `size_bytes`.
- Document listing: full version metadata plus `department_id`; see [API](api.md).
- Search result: `search_id`, `result_type` (`evidence`/`evidence_gap`), `chunks` with provenance, score, and permissions.
- CSV import: `import_id`, `inserted`, `updated`, `unchanged`, and `rejected` array of `{row, reason, raw}`. Row numbers start at 2 after the header.
- Spending: `department_id`, `start`, `end`, `currency`, `source_key`, `consulting`, `operational`, `unresolved`, `budget`, `consulting_share_percent`. Amounts and percentage are decimal strings.
- Migration: list of newly applied migration filenames; CLI wraps it as `applied`.
- Seed: table-to-inserted-count dictionary; CLI wraps it as `inserted`.
- PDF extraction: Python list of `(page_number, text)` tuples; not a public HTTP response.
- Engine result union: EngineSuccess, EngineNeedsInput, or EngineFailure, selected by `result_type`. A main-branch evidence gap uses EngineNeedsInput, not a fourth variant.
- Data repository result union: EngagementFound or EngagementNotFound, selected by `result_type`; missing and forbidden engagements intentionally share the same result.

Engine usage units are approximate whitespace-split counts, not provider token
counts or billing totals. `model_calls` reflects the adapter counter supplied by
the caller, so it can be nonzero if the same adapter was reused earlier.

## CSV, manifest, and budget inputs

CSV must be UTF-8 (optional BOM) with exactly these header names (order can vary):

```text
transaction_id,vendor,department,engagement_id,amount,currency,paid_on,classification,rationale
```

- `transaction_id`: stable source transaction ID; may be blank for conservative composite identity.
- `vendor`, `department`: exactly one known match by case-insensitive name or source key; ambiguous/unknown identities are rejected.
- `engagement_id`: matching UUID or blank; a supplied engagement must agree with both vendor and department.
- `amount`: finite decimal with at most two decimal places and absolute value below 10^16; negative refunds allowed.
- `currency`: USD only in this importer.
- `paid_on`: ISO date.
- `classification`: consulting, operational, or unresolved.
- `rationale`: nonblank reason for that classification.

Manifest requires keys `source_key`, `title`, `issuer`, `date`, `location`,
`fiscal_period`, and `access_status`. Unknown descriptive attributes may be null;
source_key must match letters/digits/dot/underscore/hyphen and location must be
truthy. The importer retains metadata; it does not apply DocumentInput's access
model to the CSV manifest. See [fixture manifest](../../tests/fixtures/week2/manifest.json).

The spending budget object supplies `department_id`, `start`, `end`, `currency`,
`source_key`, and positive finite `amount`. Its scope must exactly match the
function arguments. See [budget fixture](../../tests/fixtures/week2/budget.json).

## Other file inputs and artifacts

- PDF file: see [upload/extraction workflow](workflows.md); metadata is DocumentInput.
- Engine assignment JSON and mock response JSON: Assignment and Report shapes above, loaded from paths by the runner/adapter.
- SQL migration files: ordered `.sql` source with recorded checksum; applied once.
- Week 1 seed fixture: fixed department/vendor/engagement/payment dictionaries with stable source keys and UUIDs.
- Retrieval evaluation JSON: labeled query populations consumed by the demo, with held-out queries distinguished from measured queries.
- `prompts/consulting_v1.txt`: prompt artifact; the saved-response adapter does not send it to an external model.
- `.env` and command arguments: documented in [Operations](operations.md).
- Generated frontend: `apps/web/dist`; served only if present at app construction.
- Validation/demo JSON and command logs: generated under `evidence/local` by default; historical committed evidence is under contributor/week directories.

For exact published machine-readable data input schemas, use
[contracts/data/v1](../../contracts/data/v1) and
[contracts/data/v2](../../contracts/data/v2). Keep their examples aligned with
model changes using the export commands in [Operations](operations.md).
