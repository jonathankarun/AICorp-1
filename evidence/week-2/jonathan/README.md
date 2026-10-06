# Week 2 validation evidence

All inputs are fictional. Implementation commit: `90d2395` (full SHA in
`source-manifest.json`). The evidence commit adds these records without changing
the tested implementation. This is local automated reproduction, not a claim
that a teammate or City reviewer has signed off.

## Results

- **40 Python tests passed**, including real PostgreSQL, API, engine boundary,
  contract, and Week 1 regression checks.
- **TypeScript check and production frontend build passed.**
- **2 Chromium workflow tests passed** using the real API and a disposable database.
- **Week 1 validator passed**: the original two-payment fixture remains $300.
- **Week 2 financial demo passed**: $280 consulting, $500 operational, $50
  unresolved, and 2.80% of the matching $10,000 budget. Repeat import reports
  five unchanged payments with no new insertions.
- **Retrieval baseline:** 6/7 answerable development queries hit the relevant
  document in the top five (85.7%). All three no-evidence/forbidden cases passed.
  Two holdout cases were deliberately not run. The vocabulary-mismatch query
  “turnaround bottlenecks” failed and is retained in `demo.json`.
- **Live model quality comparison:** pending authorization; zero paid calls.

## Files and reproduction

- `expected_outputs.md`: expectations written before validation.
- `validation.txt`: captured output from the final Python tests, frontend build,
  and Chromium checks. The `httpx` deprecation warning comes from the installed
  Starlette test client. The PDF EOF warning is from the intentionally corrupt
  upload fixture; that test confirms a controlled failed state.
- `demo.json`: complete actual import/retrieval records, generated IDs, expected
  relevant IDs, returned IDs, rejected-row example, financial scope, and PDF hash.
- `demo-output.txt`: compact financial and retrieval summary.
- `week1-regression.json` / `week1-regression.txt`: expected/actual original checks.
- `browser.png`: inspected browser state showing saved data, a ready source,
  corrupt-file guidance, and an evidence gap.
- `source-manifest.json`: SHA-256 fingerprints of tracked implementation and
  fixture files at the source commit, excluding evidence files.

Commands run from the repository root:

```bash
.venv/bin/python -m pytest --run-data -q
npm run build --prefix apps/web
.venv/bin/python scripts/test_week2_browser.py
.venv/bin/python -m backend.data.week2_demo --output evidence/week-2/jonathan/demo.json
.venv/bin/python -m backend.data.validate --output evidence/week-2/jonathan/week1-regression.json
```

For a new run, prefer output paths under ignored `evidence/local/` so the frozen
submission remains intact. Each database validation/browser runner uses a fresh
random database and removes it on completion. Generated document/assignment IDs
can differ between runs; expected IDs are resolved against each run's corpus.

## Interpretation

The numerical relevance fraction is a tiny synthetic development baseline, not
City quality acceptance. The failed query remains a reason to investigate
vocabulary before adding semantic search. Permissions are proven for the local
department-scoped fixture policy, not an official identity provider. Team
contract adoption and an independent teammate walkthrough remain pending.
