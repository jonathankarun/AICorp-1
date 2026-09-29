# Jonathan Week 1 handoff

Week 1 runs September 27–October 3, 2026. The deliverable is a small PostgreSQL
database that another teammate can rebuild, seed twice, query, and validate.
All included records are fictional. The Week 1 base total is **300.00 USD**.

## Reading order

1. [Setup and commands](setup.md): install, start, migrate, seed, look up a record,
   run tests, and recover from common setup problems.
2. [Schema and data dictionary](schema.md): relationship diagram, every field,
   null rules, source references, and database constraints.
3. [Classification and provenance](classification.md): provisional consulting
   classification rules and how facts retain their origin.
4. [Repository handoff](../../contracts/data/v1/README.md): inputs, outputs,
   stable IDs, access context, and the differences from Jai's mock engine.
5. [Explanation and demonstration](explanation.md): a short presentation,
   detailed code walkthrough, and likely technical questions.
6. [Validation evidence](../../evidence/week-1/jonathan/README.md): expected
   versus actual results, test outputs, source commit, and reproduction commands.

## Deliverables mapped to the assignment

- **Relationships and diagram:** `schema.md` and the six domain tables in
  `backend/data/migrations/001_initial.sql`.
- **Migration and constraints:** `backend/data/db.py` applies versioned SQL in a
  transaction, records its checksum, and detects changed migration history.
- **Repeatable seed:** `backend/data/seed.py` reads
  `tests/fixtures/data_week1.json`. It inserts one department, vendor, engagement,
  and two payments, and rejects conflicting fixture data.
- **Repository lookup:** `DataRepository.get_engagement(id, access_context)` in
  `backend/data/repository.py`, with typed results in `models.py`.
- **Success and failure validation:** `backend/data/validate.py` and
  `tests/test_data.py`, executed against new PostgreSQL databases.
- **Reproducible environment:** `compose.yaml`, `.env.example`,
  `requirements.lock`, and `scripts/setup_local.py`.
- **Handoff documentation:** these notes, machine-readable schemas and examples
  in `contracts/data/v1/`, and the recorded evidence package.

## Basis and remaining human steps

The local *AI Corps Subsystem Development Plan* and *AI Corps Weekly
Implementation Guide* define the Week 1 requirements. Jonathan is called Jonny
in those documents. The implementation uses their PostgreSQL recommendation,
UUID identifier convention, two-payment fixture, and repository boundary.

The original Word files remain in the parent Capstone `Documentation` folder.
They are planning sources; this repository contains the instructions and
evidence needed to run this implementation.

Jonathan should rehearse the demonstration and explain the code in his own
words. Yasha or Jai should follow `setup.md` on their own machine and record the
commit, environment, date, observed results, and any missing steps. A local
automated reproduction is evidence of reproducibility, but is not a claim that
a teammate has already completed this review. All three owners still need to
agree to the shared contracts. Sponsor decisions about City records, real
classification policy, external model use, and deployment remain pending.

## Scope after Week 1

Document versions and chunks have a schema, but the Week 1 seed does not contain
documents or extracted text. CSV ingestion, a two-page PDF fixture/extraction,
search, the five-payment spending example, and budget ratios are Week 2 work.
Report persistence, a complete access policy, and application integration are
later milestones. This module does not change Jai's engine behavior or add a
live model call.
