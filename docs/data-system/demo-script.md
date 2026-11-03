# Automatic capstone demo

Start the local server as described in the README, open http://localhost:8000,
and connect with the local token. Click **Run demo**. No uploads, typing, or
manual reviews are needed.

The backend performs the real operations first, then the browser presents their
captured results in six stages, automatically advancing every six seconds:

1. **Ingest the PDF:** validates the bundled fictional PDF, stores its bytes,
   extracts pages, and creates searchable chunks. Shows actual extracted text.
2. **Store and read the assignment:** writes an example assignment, pins the PDF
   version, and reads it back from PostgreSQL in the same transaction.
3. **Retrieve evidence:** searches `timeline` in that source version with the
   existing access checks, returning the passage about six weeks and its page.
4. **Display the original source:** shows the stored PDF for comparison. This
   display does not claim that a human verified or approved the evidence.
5. **Calculate spending:** imports the five bundled CSV payments under a unique
   run key and calculates $280 consulting, $500 operational, $50 unresolved,
   and 2.80% of the matching $10,000 October budget, including the -$20 refund.
6. **Record a sample correction:** a clearly labeled scripted decision classifies
   the sample $50 as consulting, yielding $330 and 3.30%, with an actual audit entry.

Uncheck **Advance automatically every 6 seconds** before or during playback to
control the pace with **Next** and **Previous**. Clicking a stage pauses playback.
**Run demo again** executes a fresh run, always starting from the same fixture.
If an error appears, fix the connection and retry; no partial demo records persist.

## Isolation and limits

`POST /api/v1/demo/run` requires the local token, department access, and a reviewer
or administrator role. It uses the existing ingestion, assignment, retrieval,
import, spending, and correction services inside a rollback-only transaction.
Unique document IDs and import keys avoid touching existing user records. Even
on failure, temporary records roll back. Audit sequence numbers may advance,
but no demo audit rows remain. No AI model is called.

The UI displays captured results after execution, not a live progress stream.
The demo proves database writes/read-back inside a transaction; it does not claim
those temporary records survive a reload. Use the manual workspace below to
show permanent assignments, uploads, and corrections. Report storage/reviews,
recovery, and production integration are outside the automatic walkthrough.

## Bundled files for optional manual exploration

- `tests/fixtures/week2/engagement.pdf`: upload in the manual workspace, select the
  ready source, save an assignment, and search `timeline`.
- `tests/fixtures/week2/payments.csv`: imported automatically by the guided run.
- `tests/fixtures/week2/manifest.json` and `budget.json`: source metadata and the
  matching spending budget; the backend reads these automatically.

All records are fictional. No custom PDF or CSV is needed for the automatic demo.

## Verification

Run `.venv/bin/python scripts/validate_data.py --disposable --browser`.
Backend coverage checks repeatability, access rejection, and preservation of a
previously corrected payment and all affected table counts. Browser coverage
checks manual stepping, automatic advance, replay, source display, and API failure.
Local logs and screenshots are saved under `evidence/local/`.
