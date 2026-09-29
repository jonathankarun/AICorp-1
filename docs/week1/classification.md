# Provisional classification and provenance rules

These are Week 1 engineering defaults, not a sponsor-approved City policy.
The fixture explicitly labels its two payments as consulting and is entirely
fictional. It proves data handling, not a conclusion about actual City spending.

## Classify the service, not just the firm

- **Consulting:** evidence identifies advice, analysis, recommendations, or a
  consulting deliverable for the transaction or its known engagement.
- **Operational:** evidence identifies ongoing operations or another service
  outside the agreed consulting definition.
- **Unresolved:** evidence is absent, conflicting, or too broad to classify.
  Preserve the transaction and state what is missing.

Attach the rationale and original transaction reference. A vendor can provide
mixed services. Do not classify all its transactions from its name alone.
For future imports, source transaction IDs should include the source-system
namespace. Matching date, amount, and vendor is not a safe unique key.

## Money and missing links

Payments, contract commitments, budgets, and estimates are different quantities.
This Week 1 schema stores actual fixture payments only. Sum only comparable
currencies. Refunds use negative values, never silent deletion or absolute values.
Keep an unknown engagement link null. A known vendor is still required; unknown
vendors should be resolved or quarantined by the future importer.

Week 1: `100.00 + 200.00 = 300.00 USD`. Week 2 plans to add a `-20.00`
consulting refund, `500.00` operational transaction, and `50.00` unresolved
transaction. The future consulting subtotal would then be `280.00`; the budget
share would be `2.8%` only with the specified matching `10,000.00` budget.
No budget table or ratio calculation is implemented in Week 1.

## Evidence origin and permissions

Every seeded entity includes a `fixture://` source reference and stable source
key. These URIs label local synthetic records; they are not public City URLs.
Document versions provide source URI, title, issuer/date when known, byte hash,
extraction version, and access status. Chunks retain version and page.

Read access and permission to send text to an external model are separate.
Unknown access defaults to no external use. Week 1 does not send documents to a
model and does not implement a full document-access policy. The engagement
repository filters by department permissions supplied by a trusted caller.

## Decisions still required

Confirm the actual consulting definition, fiscal-period boundaries, source
permissions, reviewers, and treatment of ambiguous transactions with the team
and sponsor. Later migrations need review attribution and an audit trail for
classification corrections. Do not interpret the current `classification_reason`
field as a complete approval history.
