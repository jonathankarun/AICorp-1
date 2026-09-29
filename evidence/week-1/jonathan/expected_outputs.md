# Jonathan Week 1 expectations

These expectations were written before running the new validation. Inputs are
`tests/fixtures/data_week1.json`, containing fictional records only.

- Start a newly created empty PostgreSQL test database; apply `001_initial.sql` once.
- First seed inserts one department, one vendor, one engagement, and two payments.
- Payment values are exactly `100.00` and `200.00` USD; SQL sum is exactly `300.00`.
- A second seed inserts zero records and preserves both amounts and every ID.
- A second migration run applies zero migrations.
- The permitted engagement lookup returns the fixture's vendor and department.
- A missing UUID returns `result_type: not_found`, not an exception.
- A user without the department permission gets the same not-found result.
- An attempted payment referencing a nonexistent engagement is rejected with
  PostgreSQL foreign-key SQLSTATE `23503`; the payment count remains two.
- A nonexistent vendor and a mismatched engagement/vendor pair are also rejected.
- A payment with a known vendor and unknown engagement can retain a null link.
- Document versions require provenance; chunks must reference an existing version.
- A changed seed conflicts explicitly and rolls back any partial seed changes.
- Existing Jai engine tests continue to pass without live API calls.

Week 1 does not insert the refund, operational payment, unresolved payment, or
budget planned for Week 2. `280.00` and `2.8%` are not Week 1 results.
