# Week 1 data repository contract

Status: implemented and tested for Jonathan's data module; proposed for team
adoption. This does not claim that Yasha and Jai have approved a frozen shared
contract or connected their components.

## Call and results

```python
from uuid import UUID
from backend.data.db import connect
from backend.data.models import AccessContext
from backend.data.repository import DataRepository

context = AccessContext(
    actor_id=UUID("50000000-0000-4000-8000-000000000001"),
    allowed_department_ids=(UUID("10000000-0000-4000-8000-000000000001"),),
)
with connect() as connection:
    result = DataRepository(connection).get_engagement(
        "30000000-0000-4000-8000-000000000001", context
    )
    print(result.model_dump_json(indent=2))
```

- Input: UUID engagement ID plus a typed `AccessContext` containing actor UUID
  and allowed department UUIDs. Empty department permissions grant no access.
- Success: `result_type: engagement`, `schema_version: 1.0`, and an engagement
  containing its vendor and department records with source IDs/references.
- Absent or inaccessible ID: `result_type: not_found`, requested UUID, stable
  code `engagement_not_found`, and the same message for either case.
- Invalid UUID: `ValueError` at this internal Python boundary. A future HTTP
  adapter should validate request input and map this to an input error.
- Database outage: a driver exception reaches the caller; the local CLI maps it
  to a safe `database_error` and exit code 1. The future API owns HTTP error mapping.

The query applies the permission filter in SQL. The caller must derive context
from authenticated server state. `actor_id` records the caller's claimed context
but Week 1 does not authenticate it or implement an audit log. Never accept the
CLI's user-supplied permissions as a deployed authorization mechanism.

The repository accepts a connection so callers control its transaction lifetime.
It does not create a global connection or commit an unrelated caller's work.
No payments are joined into the lookup, so returning relationships does not
accidentally multiply payment rows or imply a spending calculation.

## Machine-readable handoff

- `access-context.schema.json`: JSON Schema generated from `AccessContext`.
- `engagement-result.schema.json`: success and not-found union schema.
- `access-context.example.json`: fixture context for the success example.
- `engagement-found.example.json`: expected relationship lookup response.
- `engagement-not-found.example.json`: expected missing-ID result.

Regenerate these files with:

```bash
.venv/bin/python -m backend.data.export_contracts
```

`tests/test_data_contracts.py` verifies that the committed schemas/examples match
the current Python types. JSON IDs are strings. Unrecognized fields are rejected.
Future changes to fields or permissions require agreement and updated examples.

## Stable fixture IDs

- Department: `10000000-0000-4000-8000-000000000001`, source key `dept-fixture-001`.
- Vendor: `20000000-0000-4000-8000-000000000001`, source key `vendor-fixture-001`.
- Engagement: `30000000-0000-4000-8000-000000000001`, source key `engagement-fixture-001`.
- First payment: `40000000-0000-4000-8000-000000000001`, source key `payment-fixture-001`.
- Second payment: `40000000-0000-4000-8000-000000000002`, source key `payment-fixture-002`.
- Local test actor: `50000000-0000-4000-8000-000000000001`; no persisted users table yet.

The fixture file is the authoritative seed input. Display names can change in
future approved migrations/imports without being used as record identities.

## Handoff to Jai

Jai's Week 1 mock uses text labels such as `dept-fixture-001` as IDs; the data
module follows the plan's UUID convention and retains that label as `source_key`.
The label and UUID are not interchangeable. Agree on a boundary mapping or update
the shared fixture contract before connecting the engine. No silent conversion
or engine schema rewrite is included here.

His fixed `doc-fixture-v1` and `chunk-fixture-001/002` evidence is not inserted
into this database. Document ingestion and search are Week 2 work. The existing
engine still uses its own mock evidence repository. Its `EvidenceChunk` also
differs from the plan's content-hash/locator contract; agree before integration.

## Handoff to Yasha

Use the typed repository instead of duplicating its joins. Map authenticated
department membership into `AccessContext`, serialize Pydantic models, and map
missing/hidden resources consistently. No FastAPI endpoint is added by this data
deliverable. Assignments, jobs, reports, document upload, and review tables need
later schema requests coordinated through Jonathan.

## Questions for the team

1. Adopt UUID IDs with source keys, or agree on a coordinated contract change?
2. Confirm which department memberships are permitted for each authenticated actor.
3. Agree on document locators, content hashes, and external-model permission fields.
4. Review the proposed lookup response with the API and engine owners.

These are review items, not blockers for running the independent Week 1 database.
