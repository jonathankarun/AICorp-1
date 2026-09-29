# Explain and demonstrate Jonathan's Week 1 work

The result is a reproducible database foundation for the consulting tool. It
stores known relationships, exact fixture payments, and the structure needed
for traceable source evidence. The successful demonstration ends with the same
two payments and 300.00 USD total after repeated setup, a correct linked lookup,
and rejection of a payment that points to nonexistent work.

Use this guide to understand the code and rehearse. The implementation was
prepared with Codex assistance. Describe that assistance according to your
course's expectations, and explain the behavior you have personally run and
understood. Do not claim that a teammate or sponsor has reviewed it until they do.

## Three-minute presentation

### First 30 seconds: goal and scope

“My Week 1 subsystem is the database foundation. The consulting engine will
eventually need reliable records about departments, firms, engagements,
payments, and documents. This week I focused on making a small database that
can be rebuilt and checked with known results. All current data is fictional.”

### Next 45 seconds: design

“The schema separates a department, a vendor, and an engagement. Payments point
to a vendor and optionally an engagement. Primary keys identify each record;
foreign keys prevent references to records that do not exist. The payment's
vendor must also agree with the engagement's vendor. Money is stored as an
exact decimal. Document versions and chunks have their own identities so later
citations can refer to a specific version and page.”

### Next minute: working proof

Run the validator:

```bash
.venv/bin/python -m backend.data.validate
```

“This command creates a new empty PostgreSQL database. It applies the migration
and inserts one department, one vendor, one engagement, and payments of 100 and
200 dollars. It then repeats migration and seeding. The counts stay unchanged
and the total remains exactly 300.00. It checks the linked engagement lookup,
checks missing and unpermitted IDs, and tries an invalid foreign-key insert.
PostgreSQL rejects that insert. Each expected and actual result is saved as JSON.”

### Final 45 seconds: interface and limits

“Yasha and Jai can call `get_engagement` instead of writing their own SQL joins.
The response is a typed engagement with its vendor and department, or a typed
not-found result. The caller supplies trusted access context. This is not yet
City authentication, document ingestion, or full application integration. Next
we need to agree on the ID contract and add the Week 2 importer and search.”

## Detailed walkthrough for a longer review

### 1. Show the input before showing the code

Open `tests/fixtures/data_week1.json`.

- Point to `synthetic: true` and the fictional names.
- Identify the stable UUIDs and source keys.
- Trace each payment's vendor and engagement IDs to the matching parent rows.
- Explain why amounts are strings in JSON: they enter Python as exact Decimal
  values rather than an intermediate binary floating-point number.
- State the expected counts and `100.00 + 200.00 = 300.00` before running anything.

The fixture is small on purpose: someone can independently predict its answer.
It is not an import of actual City records or evidence of financial savings.

### 2. Explain the schema

Open `docs/week1/schema.md` and its diagram, then
`backend/data/migrations/001_initial.sql`.

Start with departments/vendors, then engagements, then payments. Explain a
primary key as a record's stable identity. Explain a foreign key as a rule the
database enforces about an existing related record. UUIDs avoid depending on a
display name and follow the proposed shared contract.

The payment relationship has a useful additional rule: both the engagement and
vendor must agree. A valid vendor ID and valid engagement ID are not enough if
they refer to different firms. The composite foreign key prevents that mismatch.

An unknown engagement can remain null. That keeps the transaction without
inventing a relationship. The vendor remains required. Negative amounts are
allowed so future refunds are not discarded. Classification belongs to the
transaction rather than automatically to the firm.

The document tables are a foundation only. A document version records provenance;
a chunk points to that version and a page. The append-only triggers reject
updates/deletes. No source PDF has been extracted or seeded yet. Future access
policy changes need a separate mutable policy structure rather than rewriting
historical source content.

### 3. Explain a migration

Open `backend/data/db.py`, function `migrate`.

“A migration is a saved, versioned instruction for creating or changing the
database. This runner discovers numbered SQL files, hashes their exact contents,
and records what it applies. On a second run it skips the same migration. If
someone edits an already-applied file, the checksum mismatch stops the run so
different machines do not silently have different histories.”

The runner uses a transaction and a PostgreSQL advisory lock. The transaction
makes the schema change and history record succeed together or roll back
together. The lock serializes competing migration processes. Explain that future
changes belong in a new migration rather than an edit to `001_initial.sql`.

### 4. Explain repeatable seeding

Open `backend/data/seed.py`, function `seed`.

1. Load the fixed fixture.
2. Convert ID strings to UUIDs, amounts to Decimal, and dates to date objects.
3. Insert parent records before their dependent records.
4. Use the unique source key with `ON CONFLICT ... DO NOTHING` to avoid duplicates.
5. Read the existing row and compare all seeded fields with the fixture.
6. If a row conflicts, raise an error and roll back the whole seed transaction.

The comparison matters: silently skipping a changed amount would make setup look
successful while preserving unexpected data. The seed never guesses that two
payments are the same just because their amount and date match.

Demonstrate twice:

```bash
.venv/bin/python -m backend.data.cli seed
.venv/bin/python -m backend.data.cli seed
```

On the already-initialized development database both report zero new inserts.
The standalone validator records the initial insertion and repeated insertion
in a new database so the full proof remains visible.

### 5. Explain the repository boundary

Open `backend/data/repository.py`, then `backend/data/models.py`.

`DataRepository` accepts a database connection. `get_engagement` validates the
UUID, joins the engagement to its vendor and department, and applies the allowed
department filter in the SQL query. It constructs a typed response rather than
returning an arbitrary database row.

Explain parameter binding: input values are passed separately from the SQL
statement, so a value does not become executable SQL syntax. Invalid UUIDs are
also rejected before querying. The result exposes source references so callers
can preserve origin information.

Show `contracts/data/v1/engagement-found.example.json`. Success and not-found
results are distinguishable by `result_type`. Missing and inaccessible IDs share
the same not-found message. That avoids disclosing a hidden engagement through
a different error response.

The context is a trust boundary. The CLI lets a developer supply it for tests;
a deployed API must derive it from an authenticated session. The database
bootstrap role is not a production authorization design. No row-level security
or full user management is claimed here.

### 6. Explain the validation evidence

Open `evidence/week-1/jonathan/expected_outputs.md` first, then the actual JSON
and pytest log. Explain the difference between an expected answer and an
observed answer. The validator records them separately and exits nonzero on
a mismatch; it does not simply print a reassuring success message.

Walk through:

- Empty database → migration → first seed.
- Repeated seed and unchanged counts/amounts.
- Exact Decimal total and currency.
- Permitted lookup and linked parent IDs.
- Missing ID and inaccessible department.
- Invalid engagement FK rejected with SQLSTATE `23503`.
- Unchanged counts after the rejected write.

Additional integration tests exercise conflicting seeds with rollback, changed
migration history, failed migration rollback, unknown vendors, inconsistent
vendor/engagement pairs, nullable links, exact refunds, invalid numeric values,
document defaults, orphan chunks, and immutable evidence. The engine tests
continue to verify Jai's mock path independently.

The temporary database helper creates a new random database and only deletes
the database it just created. This lets failures be tested without resetting
the working fixture database. Tests with no `--run-data` are not full acceptance.

### 7. Explain what teammates receive

Show `docs/week1/README.md` and `contracts/data/v1/README.md`.

Yasha gets a connection/repository method, typed responses, and startup commands.
Jai gets stable data IDs and the planned repository boundary. His current engine
still uses mock evidence; it has not been silently switched to this database.
The department source key matches his text fixture label, but the actual
database identity is a UUID. The team needs to agree on that mapping.

## Questions you should be able to answer

**Why PostgreSQL instead of a spreadsheet or only JSON?**
The project needs linked records, constraints, transactions, and repeatable
queries. JSON remains useful for small test inputs, while PostgreSQL enforces
relationships and exact values across stored records.

**Why no pgvector yet?**
Week 1 is about trustworthy storage. The plan calls for keyword retrieval first
and semantic retrieval only if measured relevance failures justify it.

**Why not use a float for money?**
Binary floating point can approximate decimal fractions. PostgreSQL NUMERIC and
Python Decimal preserve the fixture's cent values and exact sums. The JSON
boundary uses decimal strings. Precision checking still belongs in the future
importer because NUMERIC with a fixed scale rounds more precise inputs.

**What prevents duplicate imports?**
For this seed, stable unique source keys plus insert-on-conflict handling. A
changed existing row triggers an explicit conflict. A full source importer and
traceable correction workflow remain future work.

**What if two legitimate payments have the same amount?**
They have different transaction IDs/source keys and must remain separate rows.
Deduplicating by amount would lose real transactions.

**What does 300.00 prove?**
It proves the two known fixture amounts survived storage and repeat setup
without duplication. It does not prove the real City spending total, a budget
share, consulting savings, or LLM report quality.

**Why is the plan's 280.00 not the Week 1 seed total?**
The -20.00 refund is part of Week 2. A separate disposable test shows the schema
can represent refunds, but the Week 1 seed still has exactly two payments.

**Do document hashes prove the source is true?**
No. A hash identifies content and helps detect changes. It does not establish
truth or relevance. The future importer must compute the hash, and reviewers
must assess evidence quality.

**Does a permission field secure every document?**
No. This week only the engagement lookup enforces its supplied department filter.
Future retrieval, downloads, exports, and external model calls must enforce the
appropriate policies. Unknown external-use permission defaults to false.

**Does a passing test mean the whole application works?**
No. These tests validate the database foundation and preserve the existing mock
engine checks. UI/API integration and real source/model evaluation are later work.

## Your preparation checklist

- Run setup and the full validation commands yourself.
- Trace both fixture payments into the schema and explain every foreign key.
- Demonstrate success and missing-ID lookup without changing code.
- Predict the effect of a different amount, a duplicate source key, and an invalid ID.
- Read the actual failed-insert check and explain why rejection is a passing result.
- Ask Yasha or Jai to reproduce setup and record their result.
- Record the team's ID/contract decisions and sponsor questions separately.
- Use the source commit and evidence in your submission, plus a recording or
  screenshots if your course asks for them. Screenshots supplement the runnable checks.
