# Expected outputs

Written before the Week 3 demo and final checks:

- Full existing backend suite plus initial Week 3 tests: 47 pass, no failures.
- Expanded Week 3 suite: 10 pass, including matching exported schemas, concurrent
  report saves, and all relationship kinds.
- Demo: two specialties and two documents; unchanged $300 total from the two Week 1
  payments. PDF update creates a different version; an old citation still resolves
  the original version/text. Missing source rejects the save; only one report exists.
- Separate equal-payment test: three payment IDs totaling $400, even after adding
  the two specialties and two documents.
- Injected citation insert failure: no report or report version left behind.
- Concurrent writes to version 1: one saved, one version conflict.
- Browser regression: two passing tests for upload/save/reload/search and failures.
- Frontend build: exit 0.

All inputs are fictional. No paid model calls or City records are involved.
