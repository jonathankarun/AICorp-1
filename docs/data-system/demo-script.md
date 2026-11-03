# Jonathan's capstone presentation

Start Docker Desktop, then run the README setup and launch commands from the
repository root. Open http://localhost:8000 in Chrome, paste the terminal's token,
and connect. All examples are fictional; this demo needs no model key.

## Main process (about three minutes)

1. **Explain the boundary.** “My data subsystem turns documents and payment records
   into durable, traceable evidence that the consulting engine can use.” Point at
   the four process cards; counts come from the connected workspace.
2. **Ingest.** Upload `tests/fixtures/week2/engagement.pdf`. Explain that the backend
   validates the PDF, stores the original bytes and version, extracts each page,
   splits text into chunks, and indexes them. Wait for `ready`; failed uploads
   display their reason and do not become selectable evidence.
3. **Store.** Enter “Improve permit intake” and “A preliminary improvement plan”,
   select the uploaded ready source, and save the assignment. The selection pins
   a document version so later uploads do not silently replace its evidence.
4. **Retrieve.** Search `timeline`. The result contains “six weeks” and a page 1
   reference. This is permission-filtered keyword search over stored chunks.
5. **Verify.** Click **Open original PDF** and compare the passage to page 1.
   Reload and reconnect: the assignment and selected source persist. Explain that
   retrieved text and source references can now be handed to the consulting engine.

## Payment branch (about one minute)

- Load spending. The launcher imported the bundled CSV; the browser reads totals
  from the backend. A fresh example is $280 consulting (including a -$20 refund),
  $500 operational, $50 unresolved, and 2.80% of a $10,000 October budget.
- Enter a correction reason and classify the unresolved payment as consulting.
  Show $330, 3.30%, and the saved old/new categories, actor, time, and reason.
- Reload and reconnect, then load spending again to demonstrate persistence.
  If the demo already starts at $330, show the existing audit record: restarting
  intentionally preserves the review. Do not reset your database for a presentation.
- Find past work for `process`. Explain the evidence-linked facts and unknown
  outcome. These engagement totals use a different population from October spending.

## What “done” means here

The local data subsystem implements ingestion, storage, retrieval, comparable work,
spending, corrections, report versions/reviews, access checks, and verified recovery.
The browser demonstrates the main document and payment processes. Report APIs,
permissions, and recovery also have automated acceptance coverage. Production
identity, real City data, live AI generation, and whole-team integration remain
outside this local subsystem demo.

## Verification — November 3, 2026

- Full existing backend acceptance suite: 87 passed.
- TypeScript check and production Vite build: passed.
- Real Chromium workflow suite: 3 passed, including process progress, upload,
  reload persistence, retrieval, PDF preview, corrections, and outage handling.
- Latest team engine acceptance tests after synchronizing main: 8 passed.
- Rendered full-page browser screenshot reviewed for walkthrough layout.

Reproduce with `.venv/bin/python scripts/validate_data.py --disposable --browser`.
Local logs and screenshots are under `evidence/local/` and are not committed.
