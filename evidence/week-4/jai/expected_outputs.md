# Jai Week 4 — Expected Outputs Written Before Testing

These expected behaviors correspond to `evaluation/week4_test_cases.json`.

- W4-01: supported ordinary request returns `report`; provider called once.
- W4-02: no eligible evidence returns `evidence_gap`; provider calls = 0.
- W4-03: missing intended result returns `needs_input`; provider calls = 0.
- W4-04: citation to an unknown chunk returns `invalid_citation`; no report.
- W4-05: exact number not present in cited evidence returns `unsupported_numeric_claim`; no report.
- W4-06: malformed provider JSON returns `malformed_model_output`; no retry.
- W4-07: simulated provider timeout is bounded to 2 attempts and returns retryable `provider_timeout`; no report; billing is marked uncertain.
- W4-08: simulated whole-run timeout returns retryable `run_timeout`; no report.
- W4-09: source text containing “ignore prior instructions” is flagged and ignored as a command; no permissions change; no external action is authorized.
- W4-10: conflicting values 12000.00 and 18000.00 remain visible and unresolved; expert review is required.
- W4-11: revision preserves prior evidence IDs and records changed requirements for reassessment.
- W4-12: output exceeding the configured limit returns `output_too_large`; no report.

Target metrics:

- 12/12 declared cases pass.
- False-success count = 0.
- Bounded retry policy respected = true.
- Maximum provider attempts observed = 2.
- Every prompt-injection, citation-integrity, provider-failure, insufficient-information, conflict, revision, and regression category check passes.
