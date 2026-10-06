# Yasha Week 1 — Website and Integration

## Scope

Week 1 proves the browser/API boundary independently while Jonny's persistence and Jai's engine remain separate. It includes a React/TypeScript form, FastAPI health and assignment endpoints, server validation, an in-memory assignment repository, and a structured report/source view that mirrors Jai's current Week 1 report shape.

## Backend

From the repository root, using the existing `.venv`:

```bash
.venv/bin/python -m uvicorn backend.api.main:app --reload --port 8000
```

FastAPI docs: `http://127.0.0.1:8000/docs`

Run Yasha's API tests:

```bash
.venv/bin/python -m pytest tests/test_api.py -q
```

## Frontend

```bash
cd apps/web
npm install
npm run dev
```

Run frontend test/build:

```bash
npm test
npm run build
```

## Demo input

- Problem: `Create a preliminary improvement plan for a fictional city department whose intake process is inconsistent and slow.`
- Department ID: `dept-fixture-001`
- Required output / intended result: `Provide a reviewable draft plan that improves intake consistency and turnaround time.`
- Required sections: `problem_summary, findings, recommendation, implementation_steps`
- Audience: `City department manager`
- Constraints, one per line:
  - `Use a six-week implementation horizon`
  - `Use only the synthetic fixture evidence`

The frontend automatically references `doc-fixture-v1`, matching Jai's current synthetic evidence fixture.

## Known Week 1 limitation

Assignments are held in memory; restarting FastAPI clears them. Persistence is a Week 2 boundary. Jonny's UUID-vs-source-key department mapping is also intentionally left unresolved rather than guessed.
