# Week 3 validation evidence

Owner: Jonathan. Work performed October 19, 2026. This implements the next unfinished
milestone, Week 3, following the completed Week 2 rather than skipping to calendar Week 4.

See [expected outputs](expected_outputs.md), [demo results](demo.json),
[Week 3 tests](week3-tests.txt), and [browser tests](browser-tests.txt).
The demo's source SHA-256 identifies the backend Python and migration bytes used.
Its code commit is the base HEAD during work; the manifest records the implementation
commit separately once committed. Earlier Week 1/2 evidence stays unchanged.

Commands, from repository root:

```bash
.venv/bin/python -m pytest --run-data -q --tb=short
.venv/bin/python -m pytest tests/test_week3.py --run-data -q --tb=short
.venv/bin/python -m backend.data.week3_demo --output evidence/week-3/jonathan/demo.json
npm run build --prefix apps/web
.venv/bin/python scripts/test_week2_browser.py
```

The first full backend run passed all 47 tests before three additional acceptance
checks were added. The expanded Week 3 run includes those three checks. The frontend
build passed. An existing Starlette/httpx deprecation warning remains.

An initial database test attempt failed because Docker/PostgreSQL was not yet ready.
Starting Docker Desktop and `docker compose up -d --wait db` restored the environment;
the subsequent full database run passed. No application change was needed for that.

Limitations: no teammate reproduction or shared contract signoff yet; no semantic
model/configuration agreement; report UI and generation-job integration remain
pending with their respective owners. These checks establish fictional local data
behavior, not City validation.
