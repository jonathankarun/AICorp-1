# AICorp-1
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
