# Jonathan Week 1 validation evidence

The fixture is fictional. The expected answer is one department, one vendor,
one engagement, two payments, and **300.00 USD**, unchanged by a second seed.
The expected results were written before running the new validation.

## Contents

- `expected_outputs.md`: the planned success, failure, and boundary cases.
- `run_manifest.json`: source commit, date, Python version, exact commands,
  expected/actual exit codes, timing, and overall pass/fail.
- `pytest.txt`: individual results from the full suite, including Jai's tests.
- `validation.json`: each standalone check with expected/actual values, source
  fingerprint, PostgreSQL version, and lookup responses.
- `validation-output.txt`: the validator's captured console output.
- `dependencies.txt`: the installed Python dependency consistency check.

The source input is `tests/fixtures/data_week1.json`. The migration and Python
dependencies are pinned in the recorded code commit. Validation's source hash
covers the data-module Python/SQL, seed fixture, and dependency lock.
The evidence files are committed after the implementation commit, so their
`code_commit` identifies the code tested rather than their own later commit.

## Reproduce

With Docker Desktop running, at the repository root:

```bash
python3 scripts/setup_local.py
.venv/bin/python -m backend.data.validate
.venv/bin/python -m pytest --run-data -q
```

For a new full evidence recording:

```bash
.venv/bin/python scripts/record_week1_evidence.py
```

That last command updates this evidence directory. Preserve the original
recording in Git history and commit new results with their source revision.
Routine validation instead writes to ignored `evidence/local/`.

The validator and database tests create empty databases with unique names and
remove only those databases afterward. No real City records, provider calls,
paid API usage, or production credentials are used.

## Interpreting the checks

The invalid foreign-key insert is a successful test when PostgreSQL returns
SQLSTATE `23503` and the existing payment count remains two. Missing and denied
lookup tests succeed when they return `not_found`. A no-database pytest run that
skips integration checks is not the complete result.

The additional refund test uses a disposable database to establish that negative
amounts are supported. It does not add the Week 2 refund to the seed or change
the Week 1 300.00 USD result.

This package establishes the implemented local behavior. A teammate still needs
to follow the written setup independently, and the owners still need to approve
the shared ID and access-context contract. No City review is claimed.
