# Jonathan's Week 3 — comparable work and saved report evidence

This is the next implementation week after the completed Week 2, even though the
calendar is now October 19. It follows “Week 3 Jonny” in the local Weekly
Implementation Guide (October 11–17). All examples are fictional.

The data layer can now attach specialties, methods, deliverables, recommendations,
outcomes, contract values, and related engagements to source chunks. Specialties
belong to engagements and their existing vendor; a firm can have multiple specialties
across its engagements. Unknown outcomes use a null value and a reason.

Comparable-work queries accept topic, department, and specialty filters. Supplied
filters are combined with AND; topic is a case-insensitive substring of the title
or an allowed fact. Results explain which filters matched and include linked source
versions, facts, contract values, and actual payment totals grouped by currency.
Payments are summed separately before returning relationships, so two specialties
and two documents do not multiply spending. Two separate $100 payments still count
as $200. These totals cover all recorded payments for the engagement, not a fiscal
period or consulting-only budget share; use the Week 2 spending function for that.

Reports use Jai's existing `Report` model. Storage requires UUID identifiers,
an existing assignment owned by the caller, and sequential report versions starting
at 1. A report and all citations save together or roll back together. Citations must
refer to ready, authorized chunks in the assignment department and, when sources
were selected, to those exact versions. Reads recheck access. Old report versions
and citation rows reject updates/deletes. New PDFs retain the old bytes and chunks.
Saving a draft does not establish factual support or sponsor approval.

## Run it

From the repository root, with Docker Desktop running:

```bash
python3 scripts/setup_local.py
.venv/bin/python -m pytest --run-data -q --tb=short
.venv/bin/python -m backend.data.week3_demo
```

The demo creates and removes its own temporary database. Expected: two specialties,
two documents, the unchanged Week 1 total of $300, an old citation still reading
version 1 after a changed PDF creates version 2, and a nonexistent citation rejected
without an extra report. The tests also add a separate equal-amount payment and
expect $400, simulate failure during citation insertion, and check access denials.
Week 2's separate five-payment population remains $280 consulting, $500 operational,
and $50 unresolved, with a 2.8% consulting budget share.

## Files and handoff

- `backend/data/migrations/003_week3.sql` creates relationship and report tables.
- `backend/data/week3_models.py` validates fact and comparable-query inputs.
- `backend/data/history.py` exposes `add_fact`, `link_document`, `comparable_work`,
  and `resolve_chunk`. Jai can call the comparable query with server-provided context.
- `backend/data/reports.py` exposes `save_report` and `get_report` for Yasha's API work.
- `backend/data/week3_demo.py` runs the repeatable demonstration.
- `tests/test_week3.py` checks normal and failure paths against real PostgreSQL.
- [Data contract](../../contracts/data/v3/README.md) describes calls and errors.
- [Validation evidence](../../evidence/week-3/jonathan/README.md) records actual checks.

Callers own the connection transaction and commit after successful writes. Helpers
use nested transactions so a failed report/fact save cannot leave partial rows.
Use a short transaction for each request. Report writes take a per-report lock so
competing writers cannot both claim the same next version.

Frontend report screens, generation jobs, and API routes remain the other owners'
integration work. This week delivers callable repository operations; it does not
claim that those screens or the full report-generation workflow are connected.
Teammate reproduction and contract approval still need a teammate. No messages were
sent on anyone's behalf.

Semantic storage remains deferred: the Week 2 baseline records a vocabulary miss,
but there is no agreed embedding model, dimension, or chunking configuration.
Keyword retrieval still works. The comparable query favors clarity for the small
fixture corpus; batching/index tuning is future work if the corpus grows.

## Comment pass

Source files now start with a short informal explanation, with extra comments only
around decisions that are easy to miss. JSON payloads and lockfiles stay valid data
rather than receiving unsupported comments. The two applied SQL migrations stay
byte-for-byte unchanged because migration checksums include comments:

- `001_initial.sql` creates vendors, departments, engagements, payments, and immutable
  source versions/chunks. It keeps money exact and blocks broken relationships.
- `002_week2.sql` adds assignments, PDF processing jobs, preserved CSV rows, payment
  correction history, and search logs. Mutable job state is separate from evidence.
