# Week 1 expected outputs — Jai

## Success case
Input: `tests/fixtures/assignment_complete.json`

Expected before testing:
- `result_type = report`
- `status = draft`
- assignment ID is preserved
- requested consulting sections are present
- citations resolve to controlled fixture evidence IDs
- exactly one mock model call

## Meaningful failure/boundary case
Input: `tests/fixtures/assignment_rfq_only.json`

Expected before testing:
- `result_type = needs_input`
- scope questions identify missing department, intended result, and constraints
- no completed report
- zero model calls

## Invalid model-output case
Input: complete assignment + `mock_report_invalid.json`

Expected before testing:
- typed `invalid_model_output` error
- fake evidence chunk is rejected
