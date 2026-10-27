# Validation results

Validated on October 27, 2026 (America/Chicago).

- Full Python acceptance suite: **58 passed**.
- Frontend TypeScript check and production build: **passed**.
- Real-browser workflows: **3 passed**.
- Backup/restore: passed; every table matched the snapshot, including saved source bytes and report citations.
- Access checks: blocked sources were rejected by direct reads, searches, and cited reports.
- Financial check: $280 consulting became $330 after the audited $50 correction; repeating the import kept the correction.

The Python suite reports one existing Starlette/httpx deprecation warning.
The browser's deliberately broken PDF test emits an expected PDF parse warning.

Search benchmark: 10002 chunks, 30 queries before and after.
Before p95: 201.14 ms. After p95: 8.57 ms. Returned IDs matched exactly. These are local synthetic measurements.

Detailed outputs, query plans, and screenshot are in `evidence/local/`.
Repeat everything with the commands in the main guide. The final small PDF download
link addition was checked by rebuilding the frontend after the browser run.
