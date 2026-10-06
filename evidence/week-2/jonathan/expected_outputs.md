# Expected outputs — written before validation

- Week 1 validation still returns two payments totaling 300.00 in a fresh database.
- First Week 2 import inserts five rows. Second inserts zero and reports five unchanged.
- Week 2 scope: consulting 280.00, operational 500.00, unresolved 50.00, budget 10000.00, consulting share 2.80 percent.
- An invalid amount is quarantined with its raw row; a corrected explicit transaction ID updates once and records old/new values.
- Duplicate fallback identities are quarantined; distinct transaction IDs with equal amount/date/vendor remain distinct.
- PDF extraction yields nonempty chunks with page 1 and page 2 locators.
- A corrupt or blank PDF yields failed status with no usable version.
- Assignment and selections persist across connections and API restart.
- Upload over the configured limit returns 413; non-PDF returns 415; unauthenticated calls return 401.
- Hidden sources cannot be selected or retrieved. External-model-disallowed sources never reach the model adapter.
- Unrelated query returns evidence_gap; the engine requests sources with zero model calls.
- Development retrieval results report actual IDs and top-five relevant-document hits. Holdout queries remain unrun during development.
- Frontend build and real-browser success/failure workflow pass.
