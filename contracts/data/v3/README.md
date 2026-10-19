# Week 3 data handoff (additive Python repository contract)

Use the existing trusted `AccessContext`; never build permissions from request JSON.
Inputs are exported beside this file. The Week 1/2 contracts remain unchanged.

```python
from backend.data.history import add_fact, comparable_work, link_document
from backend.data.reports import save_report, get_report
from backend.data.week3_models import FactInput, ComparableInput

# this saves one detail with a source chunk that supports it
fact_id = add_fact(conn, FactInput(
    engagement_id=engagement_id, kind="method",
    value="Staff interviews", evidence_chunk_id=chunk_id,
), context)

# this returns matching work with the reasons, documents, facts, and separate money totals
cases = comparable_work(conn, ComparableInput(
    topic="permit", specialty="process", for_external_model=True,
), context)

# report is Jai's backend.engine.models.Report with real UUID IDs
version_id = save_report(conn, report, context)
conn.commit()
stored = get_report(conn, report.report_id, report.version, context)
```

`FactInput.kind`: specialty, method, deliverable, recommendation, outcome,
related_engagement, or contract_value. All require an existing allowed evidence
chunk in the engagement's department. A related engagement must also be accessible.
Contract value requires nonnegative exact `amount` and three-letter `currency`;
other kinds reject those fields. An unknown outcome has `value=None` and a nonblank
`unknown_reason`. Assertions record supplied evidence; they do not automatically
prove that the source text supports the assertion. Importers/reviewers own that check.

`link_document(conn, engagement_id, document_version_id, context)` attaches a ready
source version from the same department; repeated links do nothing. `add_fact` also
links its evidence document automatically and returns a UUID fact ID.

`comparable_work` returns a list of dictionaries with engagement/vendor metadata,
`match_reasons`, `documents`, `facts`, `payments`, and `contract_values`. Each payment
summary has `currency`, `transaction_count`, and exact Decimal `amount`. No payments
means an empty list. Each fact includes its evidence chunk, document version, and
page number. External-model searches omit facts/documents not approved for external
use. The access context still controls department membership. Limit: 1–50, default 10.
A query without filters lists accessible work and explicitly says no similarity
filter was supplied. Contract values are assertions, not summed payment totals.

`save_report` returns an immutable report-version UUID. `get_report` returns
`report_version_id`, `report_id`, `version`, `content`, `created_at`, and resolved
`citations`. A resolved source includes text, title, source URI, page/locator,
content hash, chunk ID, and document-version ID. Report reads are owner-only under
the existing local assignment policy. Storage can retain readable evidence that is
not allowed for external model use; model retrieval must still use eligibility filters.

Errors use existing `DataError`: `not_found` (404), `report_version_conflict` (409),
`invalid_report`, `invalid_citation_ids`, `citation_outside_assignment`, and
`source_not_ready_or_not_allowed` (422). Pydantic/UUID validation raises ValueError;
API adapters should translate it into 422. A failed nested save rolls back its writes.
There are no new HTTP endpoints in this contract.
