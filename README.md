# AICorp-1

City of College Station AI Corps capstone prototype. Current code includes a
Week 2 React/FastAPI data workspace, PostgreSQL ingestion/search, and Jai's
consulting engine with mock and real-data evidence adapters.
All committed fixtures are fictional; no City data or live model key is required.

## Complete code documentation

Start with the [AICorp code handbook](docs/reference/README.md) for plain-language
workflows, all input/output models, HTTP APIs, database storage, function references,
setup and recovery commands, and a separately labeled guide to unmerged team branches.

## Week 2 workspace and data integration

```bash
python3 scripts/setup_local.py
npm ci --prefix apps/web
npm run build --prefix apps/web
.venv/bin/python scripts/serve_week2.py
```

Open http://127.0.0.1:8000 and use the local token printed by the launcher.
Upload `tests/fixtures/week2/engagement.pdf`, select the ready source, save an
assignment, reload, and search its page-linked evidence.

- [Week 2 overview](docs/week2/README.md)
- [Setup, demonstration, and recovery](docs/week2/setup.md)
- [File-by-file explanation and presentation notes](docs/week2/explanation.md)
- [API/data contract](contracts/data/v2/README.md)
- [Validation evidence](evidence/week-2/jonathan/README.md)

Validate with `.venv/bin/python -m pytest --run-data -q` and
`.venv/bin/python -m backend.data.week2_demo`. The controlled Week 2 source
population yields **$280 consulting, $500 operational, $50 unresolved, and 2.8%**
of its matching $10,000 budget. Week 1's separate fixture still totals $300.

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

This command keeps the original fixed evidence and saved model response.
Week 2 adds `DataEvidenceRepository` for real UUID-backed retrieval; see the
version 2 contract. Team adoption and live-model evaluation remain pending.

## Planned architecture

The diagram below describes the planned system, not completed functionality.
The local UI/API, CSV/PDF ingestion, and keyword retrieval are implemented.
Live model integration remains conditional on authorization. pgvector
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
