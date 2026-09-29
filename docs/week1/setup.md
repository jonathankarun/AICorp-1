# Set up and run the Week 1 database

Run commands from the repository root. The development path uses Python 3.12
or 3.13, Docker Desktop with Compose v2, and PostgreSQL 17 in a container.
`requirements.lock` pins the Python package versions; `compose.yaml` pins the
database image. The evidence JSON records the exact versions used for validation.

## First setup

On Jonathan's computer the repository is at
`/Users/jonathankarun/Capstone/AICorp-1`. On another computer, clone the GitHub
repository and enter that directory.

```bash
cd /Users/jonathankarun/Capstone/AICorp-1
python3 scripts/setup_local.py
```

Open Docker Desktop before running setup. The script checks Docker, creates an
ignored `.env` with a random local password and owner-only file permissions,
creates `.venv`, installs the lockfile, starts PostgreSQL, applies the migration,
and seeds the fixture. It preserves existing `.env` files and database volumes.
Running it again must not duplicate fixture records.

The script prints each operation's result. Stop if any command fails. Do not
interpret a Python environment being created as proof that the database is ready.

The examples below use `.venv/bin/python` on macOS/Linux. On Windows use
`.venv\Scripts\python.exe` and run the setup script with an installed supported Python.
The recorded validation covers macOS and the configured Linux CI, not a Windows run.

## Configuration

Copy `.env.example` to `.env` only if configuring manually; replace the password
placeholder. Do not commit `.env`. Existing shell variables take precedence over
`.env`, so check for stale exported values if the connection differs from the file.

- `POSTGRES_USER`: local database role; default `aicorp`.
- `POSTGRES_PASSWORD`: locally generated password; never part of evidence output.
- `POSTGRES_DB`: persistent development database; default `aicorp`.
- `POSTGRES_PORT`: host port mapped to container port 5432; default `55432`.
- `PGHOST`: host used by Python; default `127.0.0.1`.

The Compose service binds to localhost. Its volume preserves records across
container restarts. The container's bootstrap role can create test databases;
it is a local development administrator, not a proposed production app role.
Use fictional fixtures only. There are no model API keys in this setup.

## Individual operations

Start the existing service:

```bash
docker compose up -d --wait db
```

Apply migrations, then seed twice:

```bash
.venv/bin/python -m backend.data.cli migrate
.venv/bin/python -m backend.data.cli seed
.venv/bin/python -m backend.data.cli seed
```

On a new database the migration reports `001_initial.sql`. Later runs report
an empty `applied` list. The first seed inserts 1 department, 1 vendor,
1 engagement, and 2 payments. A repeated seed reports zero for all four tables.
If setup already seeded the database, both commands above correctly report zero.

Look up the seeded engagement using an explicit local test context:

```bash
.venv/bin/python -m backend.data.cli lookup \
  30000000-0000-4000-8000-000000000001 \
  --actor-id 50000000-0000-4000-8000-000000000001 \
  --department-id 10000000-0000-4000-8000-000000000001
```

Expected: `result_type` is `engagement`, with the fictional vendor and department
nested in the response. The CLI context is for local testing; an API must derive
these permissions from authenticated server state.

Try a well-formed but missing ID:

```bash
.venv/bin/python -m backend.data.cli lookup \
  30000000-0000-4000-8000-000000000099 \
  --actor-id 50000000-0000-4000-8000-000000000001 \
  --department-id 10000000-0000-4000-8000-000000000001
```

Expected: `result_type: not_found` and exit code 2. Omit `--department-id` from
the successful command to demonstrate denied access: it also returns `not_found`.
Malformed UUID input is rejected by the command parser before any query.

## Validate from an empty database

```bash
.venv/bin/python -m backend.data.validate
.venv/bin/python -m pytest --run-data -q
```

The validator creates a new random database, checks the full Week 1 path, writes
`evidence/local/week1-validation.json`, and deletes only its own temporary database.
It exits 0 when all checks pass and 1 on failure. The integration tests likewise
use disposable databases; they do not clear the persistent `aicorp` database.
The role needs permission to create databases for these commands.

`pytest -q` without `--run-data` runs Jai's engine tests and explicitly skips the
database tests. It is not full Week 1 acceptance. Use `--run-data` for submission.

The GitHub Actions workflow uses a PostgreSQL service and runs both the engine
and database tests plus the standalone validator on every push/PR.

## Inspect the database without writing new code

```bash
docker compose exec db psql -U aicorp -d aicorp
```

Inside `psql`:

```sql
\dt
\d payments
SELECT source_key, amount, currency, classification FROM payments ORDER BY source_key;
SELECT currency, SUM(amount) FROM payments GROUP BY currency;
SELECT version, sha256, applied_at FROM schema_migrations;
\q
```

Use your configured role/database if you changed their defaults. `\d payments`
shows PostgreSQL's real foreign keys and exact money column.

## Stop and restart

```bash
docker compose stop db
docker compose start db
```

Stopping does not delete data. Routine validation never needs volume deletion.
Keep `.env`: changing its password does not change the password already stored
inside an initialized PostgreSQL volume.

## Troubleshooting

- **Cannot connect to Docker:** open Docker Desktop and wait until its engine is
  running, then rerun setup.
- **Port in use:** choose an unused `POSTGRES_PORT` in `.env`, then rerun setup.
- **Password authentication failed:** restore the `.env` used to initialize the
  volume, or deliberately update the role password through an authorized session.
- **Seed conflict:** an existing fixture row differs. Inspect it; the seed refuses
  to overwrite it. Use the fresh-database validator for an untouched fixture.
- **Applied migration changed:** restore the original SQL and add a new numbered
  migration. Do not alter the checksum ledger to bypass the check.
- **Permission denied to create database:** use the local Compose development
  role for tests, or have the database owner grant CREATEDB in a test environment.
- **Connection error from CLI:** check `docker compose ps` and configuration.
  The CLI intentionally does not print connection strings or driver internals.
- **Interrupted tests:** normal exceptions clean up temporary databases. A hard
  process termination may leave an `aicorp_w1_test_…` database. Identify it before
  any manual cleanup; never reset the working database to rerun tests.
