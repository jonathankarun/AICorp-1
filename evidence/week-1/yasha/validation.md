# Yasha Week 1 validation record

Purpose: prove the assignment API accepts one complete synthetic request, rejects a whitespace-only problem, and the browser can render the current Jai-compatible mock report shape.

Backend command:

```bash
.venv/bin/python -m pytest tests/test_api.py -q
```

Frontend commands:

```bash
cd apps/web
npm test
npm run build
```

Expected backend: 3 passing tests. Expected frontend: report-render test passes and production build succeeds.

Failure case: POST the valid fixture with `problem` replaced by whitespace. Expected HTTP 422 with `VALIDATION_ERROR` and zero created assignments for that test.

Limitations: in-memory assignment storage only; no live database, upload, worker, authentication, or live model call in Week 1.
