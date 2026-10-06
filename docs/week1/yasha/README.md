# Yasha — frontend subsystem

The original `yasha-week1` branch introduced a React assignment form, typed API
boundary, structured report viewer, clickable citation details, and tests.
These are now integrated with Jonathan's Week 2 workspace and Jai's Week 2/3
engine. Use [the integration guide](../../week2/frontend-integration.md) and
[shared setup](../../week2/setup.md) for current commands.

Both `backend.api.main:app` and `backend.api.app:app` now refer to the shared
API. Start it through `scripts/serve_week2.py` to configure the local token and
database. The separate unauthenticated, in-memory API has been replaced.
Assignments use real UUID department/document-version identifiers and persist
in PostgreSQL. The original mock report fixture remains only in the viewer's
unit test; the running UI displays evidence returned by the consultation API.

The historical TA script, v1 examples, and Week 1 evidence record the earlier
implementation, not the current API contract.
