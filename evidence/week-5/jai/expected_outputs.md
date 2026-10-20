# Week 5 Expected Outputs

These expectations are written before running the development fixture.

1. Both candidates receive identical assignment/evidence and an equal number of runs.
2. The duplicate-context tuning removes `w5-intake-1-duplicate` and reduces the estimated input-token count.
3. The low-cost fixture candidate records three runs, including one visible `missing_required_sections` failure.
4. The stronger fixture candidate completes all three runs and meets the configured quality gate.
5. The selected frozen configuration is the lowest-cost candidate among those that meet every gate. In the committed fixture, this is expected to be `stronger_candidate` because the low-cost candidate has a failed run.
6. The deliberately tiny budget test returns `budget_exceeded` with `provider_calls = 0`.
7. Week 4 no-evidence, fake-citation, prompt-injection, and conflicting-evidence regressions remain passing when those files are present.
8. No live API key or paid call is required for this development test.
