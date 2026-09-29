# AICorp-1

City of College Station AI Corps capstone prototype. Current code includes Jai's
Week 1 mock consulting engine and Jonathan's Week 1 PostgreSQL data subsystem.
All committed fixtures are fictional; no City data or live model key is required.

## Jonathan's Week 1 database

Start Docker Desktop and use Python 3.12 or 3.13:

```bash
python3 scripts/setup_local.py
.venv/bin/python -m backend.data.validate
.venv/bin/python -m pytest --run-data -q
```

Setup creates the local environment, starts PostgreSQL, migrates, and seeds one
department, one vendor, one engagement, and two payments totaling **300.00 USD**.
Validation rebuilds a separate temporary database and exercises success/failure
cases. The full tests include Jai's existing engine tests.

- [Week 1 deliverables and reading order](docs/week1/README.md)
- [Setup and troubleshooting](docs/week1/setup.md)
- [Schema diagram and data dictionary](docs/week1/schema.md)
- [Repository contract and fixture IDs](contracts/data/v1/README.md)
- [Technical explanation and demo script](docs/week1/explanation.md)
- [Recorded validation evidence](evidence/week-1/jonathan/README.md)

## Jai's Week 1 mock engine

After installing the shared lockfile (done by setup):

```bash
.venv/bin/python -m backend.engine.runner tests/fixtures/assignment_complete.json --output evidence/local/engine-result.json
.venv/bin/python -m pytest tests/test_engine.py -q
```

The engine still uses fixed synthetic evidence and a saved model response.
Connecting it to the database requires the shared ID/evidence contract handoff.

## Planned architecture

The diagram below describes the planned system, not completed functionality.
The UI/API, full ingestion, and live model integration are later work. pgvector
is optional after a measured keyword-search baseline.

```text
                         ┌──────────────────────────┐
                         │     Next.js / React      │
                         │      Yasha's Area        │
                         │                          │
                         │ Login / Upload / Chat    │
                         │ Sources / Report Viewer  │
                         └────────────┬─────────────┘
                                      │
                                      │ REST API
                                      ▼
                         ┌──────────────────────────┐
                         │        FastAPI           │
                         │   Shared Backend Layer   │
                         │                          │
                         │ /projects                │
                         │ /documents               │
                         │ /consult                 │
                         │ /sources                 │
                         │ /reports                 │
                         └──────┬──────────┬────────┘
                                │          │
                 ┌──────────────┘          └──────────────┐
                 ▼                                        ▼
      ┌───────────────────────┐              ┌────────────────────────┐
      │ Data / Knowledge      │              │ LLM Consulting Engine  │
      │ Jonny                 │              │ Jai                    │
      │                       │              │                        │
      │ PostgreSQL            │◄────────────►│ Retrieval / RAG        │
      │ pgvector              │              │ Prompt / Methodology   │
      │ Documents             │              │ LLM API                │
      │ Consultant DB         │              │ Citation Validation    │
      │ Spending / Contracts  │              │ Report Generation      │
      │ Ingestion Pipelines   │              │ Internal vs External   │
      └───────────────────────┘              └────────────────────────┘
```
