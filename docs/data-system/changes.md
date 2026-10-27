# What I changed, in simple terms

The main change: the database features are now usable through the local API and a
small demo. I also finished the missing correction, permission, review, and recovery
pieces from the implementation guide. Comments use the existing short, informal
style: what the code does and why it matters.

## New files

- `apps/web/src/DataDemo.tsx`: the simple spending/correction and past-work demo.
- `apps/web/src/SourcePreview.tsx`: opens the exact saved PDF behind evidence.
- `backend/data/operations.py`: changes a payment category, blocks a source, reads
  original PDFs, and records report reviews. Checks permission before doing it.
- `backend/data/demo.py`: loads fictional examples without resetting saved corrections.
- `backend/data/recovery.py`: backs up the database and tests a restore safely.
- `backend/data/benchmark.py`: measures search speed before and after indexing.
- `backend/data/migrations/004_release.sql`: adds roles, document restrictions,
  correction history, and report reviews. Audit/review rows cannot be overwritten.
- `backend/data/migrations/005_search_index.sql`: adds the measured keyword-search index.
- `tests/test_release.py`: tests these workflows and their failure cases.
- `scripts/validate_data.py`: one command to run checks and save the results.
- `docs/data-system/README.md`: setup, demo steps, maintenance, permissions, and limits.
- `docs/data-system/changes.md`: this explanation.

## Changed files

- `backend/api/app.py`: connects the data features to authenticated API routes.
- `backend/data/history.py`: hides blocked source evidence from comparable work and
  direct citation reads. Existing local changes were preserved.
- `backend/data/search.py`: hides blocked documents before searching.
- `backend/data/workspace.py`: filters blocked documents/jobs and prevents selecting
  a source from the wrong assignment department.
- `backend/data/reports.py`: turns bad IDs into understandable errors, requires new
  versions to be drafts, and includes review history when reading a report.
- `backend/data/importer.py`: keeps reviewed classifications when importing again
  and locks existing payment rows while updating them.
- `backend/data/ingestion.py`: records chunk size in the extraction configuration
  identity, so configuration changes can create new versions safely.
- `apps/web/src/main.tsx`: includes the demo, searches readable local evidence,
  shows original PDFs, and lets an upload update an existing document.
- `apps/web/src/style.css`: basic spacing and dropdown styling.
- `apps/web/tests/workspace.spec.ts`: checks the new demo and persistence in a browser.
- `scripts/serve_week2.py`: starts the full demo with the new fictional examples.
- `contracts/data/v2/openapi.json`: regenerated so the API contract matches the code.
- `README.md`: points to the finished local subsystem and its instructions.

The already-edited `tests/test_week3.py` and
`evidence/week-3/jonathan/browser-tests.txt` were left as found. Earlier changes in
`history.py` and `reports.py` were kept, not discarded.

## Steps taken

1. Read the existing code and your subsystem implementation guide.
2. Kept the working imports/search/version storage, then connected their missing API paths.
3. Added the missing permission, correction, and report-review records.
4. Built a basic UI around real database results.
5. Tested both successful operations and denied/broken/stale operations.
6. Restored a backup into a separate database and compared every saved table.
7. Measured search, added an index, and checked that results stayed identical.
8. Added repeatable validation and these plain-language instructions.
