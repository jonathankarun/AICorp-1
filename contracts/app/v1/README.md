# Yasha Week 1 application contract notes

These examples are aligned with Jai's current Week 1 `backend.engine.models` shape so the frontend/API does not create a second incompatible Assignment/Report format.

The application API adds `created_by` to its create response because identity is server-owned. Jai's engine does not currently require that field.

Known team contract gap: Jonny's data module uses UUID department IDs and retains `dept-fixture-001` as a source key, while Jai's Week 1 engine uses the text source key as `department_id`. Week 1 does not silently convert between them. Resolve that mapping with the team before Week 2 persistence integration.

Another current difference from the development-plan proposal is that Jai's Week 1 `Report` model does not yet carry `run_id`. Do not change Jai's model only for this Yasha demo; record it as a shared-contract decision for later job integration.
