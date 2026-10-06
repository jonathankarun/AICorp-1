# Branch function and model inventory

[Handbook home](README.md) · [Readable branch guide](branches.md)

Exact signatures and declared model fields in changed/new Python files relative to main. Identical source blobs are documented once across branches; the integrated branch is listed first. Common unchanged functions are in [the main reference](functions.md). Signatures are source-derived, not a promise that every internal helper is a public API.


## origin/yasha-week2 — 7d6562a


### backend/api/app.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/api/app.py)


```python
create_app(connection_factory=connect, *, context=None, token=None, local_mode=None, max_bytes=None)
```

Return expression: `app`.

Return expression: `trusted_context`.

Return expression: `JSONResponse(status_code=exc.status, content={'error': {'code': exc.code}})`.

Return expression: `JSONResponse(status_code=422, content={'error': {'code': 'invalid_request', 'fields': ['.'.join(map(str, e['loc'])) for e in exc.errors()]}})`.

Return expression: `JSONResponse(status_code=503, content={'error': {'code': 'database_unavailable'}})`.

Return expression: `{'status': 'ok', 'mode': 'local-fixture-demo'}`.

Return expression: `result`.

Return expression: `save_assignment(conn, data, ctx)`.

Return expression: `get_assignment(conn, identifier, ctx)`.

Return expression: `list_documents(conn, ctx)`.

Return expression: `{**result.model_dump(mode='json'), 'evidence': [chunk.model_dump(mode='json') for chunk in model.evidence]}`.

Return expression: `list_jobs(conn, ctx)`.

Return expression: `get_job(conn, identifier, ctx)`.

Return expression: `search(conn, data, ctx)`.


```python
create_app.lifespan(app)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
create_app.identity(authorization: str | None=Header(default=None))
```

Return expression: `trusted_context`.


```python
create_app.domain_error(request, exc)
```

Return expression: `JSONResponse(status_code=exc.status, content={'error': {'code': exc.code}})`.


```python
create_app.validation_error(request, exc)
```

Return expression: `JSONResponse(status_code=422, content={'error': {'code': 'invalid_request', 'fields': ['.'.join(map(str, e['loc'])) for e in exc.errors()]}})`.


```python
create_app.database_error(request, exc)
```

Return expression: `JSONResponse(status_code=503, content={'error': {'code': 'database_unavailable'}})`.


```python
create_app.health()
```

Return expression: `{'status': 'ok', 'mode': 'local-fixture-demo'}`.


```python
create_app.create_assignment(data: AssignmentInput, ctx=Depends(identity))
```

Return expression: `save_assignment(conn, data, ctx)`.


```python
create_app.read_assignment(identifier: UUID, ctx=Depends(identity))
```

Return expression: `get_assignment(conn, identifier, ctx)`.


```python
create_app.documents(ctx=Depends(identity))
```

Return expression: `list_documents(conn, ctx)`.


```python
create_app.consult(identifier: UUID, ctx=Depends(identity))
```

Return expression: `{**result.model_dump(mode='json'), 'evidence': [chunk.model_dump(mode='json') for chunk in model.evidence]}`.


```python
create_app.jobs(ctx=Depends(identity))
```

Return expression: `list_jobs(conn, ctx)`.


```python
create_app.job(identifier: UUID, ctx=Depends(identity))
```

Return expression: `get_job(conn, identifier, ctx)`.


```python
create_app.work(identifier)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
create_app.upload(background: BackgroundTasks, metadata: str=Form(...), file: UploadFile=File(...), ctx=Depends(identity))
```

Return expression: `result`.


```python
create_app.find(data: SearchInput, ctx=Depends(identity))
```

Return expression: `search(conn, data, ctx)`.


### backend/api/main.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/api/main.py)

No named symbols; module-level setup/script code only.


### backend/engine/demo_adapters.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_adapters.py)


**Class `ModelAdapter`** — bases: `Protocol`.

- `call_count: int` — required.

```python
ModelAdapter.generate(self, assignment: Assignment, evidence: list[EvidenceChunk], generation_context: dict[str, Any] | None=None) -> tuple[dict, UsageRecord]
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


**Class `MockModelAdapter`** — bases: .

Deterministic adapter used for repeatable demos and CI; no API key required.


```python
MockModelAdapter.__init__(self, response_path: str | Path, prompt_version: str='v1')
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
MockModelAdapter.generate(self, assignment: Assignment, evidence: list[EvidenceChunk], generation_context: dict[str, Any] | None=None) -> tuple[dict, UsageRecord]
```

Return expression: `(payload, usage)`.


### backend/engine/demo_methodology.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_methodology.py)


```python
_text_tokens(chunk: EvidenceChunk) -> set[str]
```

Return expression: `{token.strip('.,:;()') for token in text.split()}`.


```python
build_evidence_map(assignment: Assignment, evidence: list[EvidenceChunk]) -> list[EvidenceMapEntry]
```

Return expression: `entries`.


```python
calculate_cost_evidence(assignment: Assignment, repository: EvidenceRepository, query: str) -> CostEvidence
```

Return expression: `CostEvidence(min_amount=f'{min(amounts):.2f}', max_amount=f'{max(amounts):.2f}', currency=next(iter(currencies)) if len(currencies) == 1 else 'USD', fiscal_period=next(iter(periods)) if len(periods) == 1 else 'mixed', amount_type=next(iter(amount_types)) if len(amount_types) == 1 else 'mixed', source_ids=source_ids, limitation='These are historical actual payments from fictional comparison records, not a current quote or authorized spending recommendation.')`.

Return expression: `CostEvidence(min_amount=None, max_amount=None, currency='USD', fiscal_period=None, amount_type='actual_payment', source_ids=[], reason='No comparable historical cost evidence is available in the permitted fixture corpus.', limitation='No current cost estimate is inferred from missing evidence.')`.


```python
build_generation_context(assignment: Assignment, evidence: list[EvidenceChunk], repository: EvidenceRepository, query: str)
```

Return expression: `(context, evidence_map, cost_evidence)`.


### backend/engine/demo_models.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_models.py)


**Class `Assignment`** — bases: `BaseModel`.

- `assignment_id: str` — required.
- `schema_version: str` — `'1.0'`.
- `problem: str` — required.
- `department_id: str | None` — `None`.
- `intended_result: str | None` — `None`.
- `topic: str | None` — `None`.
- `required_sections: list[str]` — `Field(default_factory=list)`.
- `audience: str | None` — `None`.
- `constraints: list[str]` — `Field(default_factory=list)`.
- `selected_document_version_ids: list[str]` — `Field(default_factory=list)`.
- `request_type: Literal['problem', 'RFP', 'RFQ']` — `'problem'`.

```python
Assignment.problem_must_not_be_blank(cls, value: str) -> str
```

Return expression: `value.strip()`.


**Class `AccessContext`** — bases: `BaseModel`.

Synthetic server-derived access context used by the engine demo.

- `actor_id: str` — `'demo-user'`.
- `readable_scopes: list[str]` — `Field(default_factory=lambda: ['fixture', 'public'])`.
- `external_model_use: bool` — `True`.

**Class `EvidenceChunk`** — bases: `BaseModel`.

- `chunk_id: str` — required.
- `document_version_id: str` — required.
- `title: str` — required.
- `source_uri: str` — required.
- `locator: str` — required.
- `text: str` — required.
- `content_hash: str | None` — `None`.
- `department_id: str | None` — `None`.
- `access_scope: str` — `'fixture'`.
- `external_model_allowed: bool` — `True`.

**Class `HistoricalCostRecord`** — bases: `BaseModel`.

- `record_id: str` — required.
- `amount: str` — required.
- `currency: str` — `'USD'`.
- `fiscal_period: str` — required.
- `amount_type: Literal['actual_payment', 'contract_value', 'estimate']` — `'actual_payment'`.
- `source_ids: list[str]` — required.

**Class `CostEvidence`** — bases: `BaseModel`.

- `min_amount: str | None` — `None`.
- `max_amount: str | None` — `None`.
- `currency: str` — `'USD'`.
- `fiscal_period: str | None` — `None`.
- `amount_type: str | None` — `None`.
- `source_ids: list[str]` — `Field(default_factory=list)`.
- `reason: str | None` — `None`.
- `limitation: str | None` — `None`.

**Class `Citation`** — bases: `BaseModel`.

- `citation_id: str` — required.
- `evidence_chunk_id: str` — required.

**Class `ReportSection`** — bases: `BaseModel`.

- `name: str` — required.
- `content: str` — required.
- `citation_ids: list[str]` — `Field(default_factory=list)`.

**Class `Report`** — bases: `BaseModel`.

- `report_id: str` — required.
- `assignment_id: str` — required.
- `version: int` — `1`.
- `status: Literal['draft', 'reviewed', 'approved']` — `'draft'`.
- `sections: list[ReportSection]` — required.
- `citations: list[Citation]` — required.
- `assumptions: list[str]` — `Field(default_factory=list)`.
- `missing_information: list[str]` — `Field(default_factory=list)`.
- `expert_review_needed: list[str]` — `Field(default_factory=list)`.
- `cost_evidence: CostEvidence | None` — `None`.
- `run_id: str | None` — `None`.

```python
Report.validate_citation_references(self)
```

Return expression: `self`.


**Class `ScopeCheckResult`** — bases: `BaseModel`.

- `status: Literal['ready', 'needs_input']` — required.
- `questions: list[str]` — `Field(default_factory=list)`.
- `missing_fields: list[str]` — `Field(default_factory=list)`.

**Class `UsageRecord`** — bases: `BaseModel`.

- `provider: str` — required.
- `model: str` — required.
- `prompt_version: str` — required.
- `input_units: int` — `0`.
- `output_units: int` — `0`.
- `elapsed_ms: int` — `0`.
- `mock: bool` — `True`.

**Class `RetrievalTrace`** — bases: `BaseModel`.

- `query: str` — required.
- `filters: dict[str, Any]` — `Field(default_factory=dict)`.
- `candidate_chunk_ids: list[str]` — `Field(default_factory=list)`.
- `selected_chunk_ids: list[str]` — `Field(default_factory=list)`.
- `rejected_chunk_ids: list[str]` — `Field(default_factory=list)`.
- `selected_document_version_ids: list[str]` — `Field(default_factory=list)`.
- `context_word_count: int` — `0`.
- `max_chunks: int` — `5`.
- `max_context_words: int` — `450`.

**Class `EvidenceMapEntry`** — bases: `BaseModel`.

- `section: str` — required.
- `supporting_chunk_ids: list[str]` — `Field(default_factory=list)`.
- `gap: bool` — `False`.
- `notes: str | None` — `None`.

**Class `EngineSuccess`** — bases: `BaseModel`.

- `result_type: Literal['report']` — `'report'`.
- `report: Report` — required.
- `usage: UsageRecord` — required.
- `retrieval_trace: RetrievalTrace | None` — `None`.
- `evidence_map: list[EvidenceMapEntry]` — `Field(default_factory=list)`.
- `methodology_stages: list[str]` — `Field(default_factory=list)`.

**Class `EngineNeedsInput`** — bases: `BaseModel`.

- `result_type: Literal['needs_input']` — `'needs_input'`.
- `assignment_id: str` — required.
- `questions: list[str]` — required.
- `missing_fields: list[str]` — required.
- `model_calls: int` — `0`.

**Class `EngineEvidenceGap`** — bases: `BaseModel`.

- `result_type: Literal['evidence_gap']` — `'evidence_gap'`.
- `assignment_id: str` — required.
- `message: str` — required.
- `query: str` — required.
- `rejected_chunk_ids: list[str]` — `Field(default_factory=list)`.
- `model_calls: int` — `0`.

**Class `EngineFailure`** — bases: `BaseModel`.

- `result_type: Literal['error']` — `'error'`.
- `code: str` — required.
- `message: str` — required.
- `retryable: bool` — `False`.

### backend/engine/demo_pipeline.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_pipeline.py)


```python
validate_assignment(data: dict | Assignment) -> Assignment
```

Return expression: `data if isinstance(data, Assignment) else Assignment.model_validate(data)`.


```python
validate_report(raw_report: dict, valid_evidence_ids: set[str], required_sections: list[str] | None=None) -> Report
```

Return expression: `report`.


```python
run_engine(data: dict | Assignment, model_client: ModelAdapter, repository: EvidenceRepository | None=None, access_context: AccessContext | None=None, *, max_chunks: int=5, max_context_words: int=450) -> EngineResult
```

Return expression: `EngineSuccess(report=report, usage=usage, retrieval_trace=retrieval.trace, evidence_map=evidence_map, methodology_stages=METHODOLOGY_STAGES)`.

Return expression: `EngineNeedsInput(assignment_id=assignment.assignment_id, questions=scope.questions, missing_fields=scope.missing_fields, model_calls=getattr(model_client, 'call_count', 0))`.

Return expression: `EngineEvidenceGap(assignment_id=assignment.assignment_id, message='No eligible evidence was retrieved. Add an allowed source, broaden the approved corpus, or clarify the request before generation.', query=retrieval.trace.query, rejected_chunk_ids=retrieval.trace.rejected_chunk_ids, model_calls=getattr(model_client, 'call_count', 0))`.

Return expression: `EngineFailure(code='invalid_assignment', message=str(exc), retryable=False)`.

Return expression: `EngineFailure(code='invalid_model_output', message=str(exc), retryable=False)`.


### backend/engine/demo_repository.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_repository.py)


```python
_tokens(text: str) -> set[str]
```

Return expression: `normalized`.


**Class `EvidenceRepository`** — bases: `Protocol`.


```python
EvidenceRepository.search_evidence(self, query: str, *, selected_document_version_ids: list[str] | None=None, department_id: str | None=None) -> list[EvidenceChunk]
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
EvidenceRepository.get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


**Class `FixtureEvidenceRepository`** — bases: .

Keyword baseline used until Jonny's Week 2 search contract is available.


```python
FixtureEvidenceRepository.__init__(self, evidence: list[EvidenceChunk] | None=None)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
FixtureEvidenceRepository.search_evidence(self, query: str, *, selected_document_version_ids: list[str] | None=None, department_id: str | None=None) -> list[EvidenceChunk]
```

Return expression: `[item[2] for item in scored]`.


```python
FixtureEvidenceRepository.get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]
```

Return expression: `HISTORICAL_COSTS.copy()`.

Return expression: `[]`.


**Class `NoCostFixtureRepository`** — bases: `FixtureEvidenceRepository`.

Week 3 failure fixture: relevant operational evidence exists, but comparable cost evidence does not.


```python
NoCostFixtureRepository.search_evidence(self, query: str, **kwargs) -> list[EvidenceChunk]
```

Return expression: `[item for item in super().search_evidence(query, **kwargs) if item.document_version_id != 'doc-cost-v1']`.


```python
NoCostFixtureRepository.get_historical_costs(self, query: str, department_id: str | None) -> list[HistoricalCostRecord]
```

Return expression: `[]`.


```python
get_fixture_evidence(_assignment=None) -> list[EvidenceChunk]
```

Backward-compatible helper retained for Week 1 examples.


### backend/engine/demo_retrieval.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_retrieval.py)


**Class `RetrievalBundle`** — bases: .

- `evidence: list[EvidenceChunk]` — required.
- `trace: RetrievalTrace` — required.

```python
prepare_query(assignment: Assignment) -> str
```

Return expression: `' '.join((part.strip() for part in parts if part and part.strip()))`.


```python
_select_context(query: str, candidates: list[EvidenceChunk], access_context: AccessContext, *, selected_document_version_ids: list[str] | None=None, max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `RetrievalBundle(evidence=selected, trace=trace)`.


```python
retrieve_for_assignment(assignment: Assignment, repository: EvidenceRepository, access_context: AccessContext, *, max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `_select_context(query, candidates, access_context, selected_document_version_ids=assignment.selected_document_version_ids, max_chunks=max_chunks, max_context_words=max_context_words)`.


```python
retrieve_query(query: str, repository: EvidenceRepository, access_context: AccessContext, *, selected_document_version_ids: list[str] | None=None, department_id: str | None='dept-fixture-001', max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `_select_context(query, candidates, access_context, selected_document_version_ids=selected_document_version_ids, max_chunks=max_chunks, max_context_words=max_context_words)`.


### backend/engine/demo_runner.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_runner.py)


```python
main() -> int
```

Return expression: `0 if result.result_type != 'error' else 1`.


### backend/engine/demo_scope.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/demo_scope.py)


```python
check_scope(assignment: Assignment) -> ScopeCheckResult
```

Return expression: `ScopeCheckResult(status='ready')`.

Return expression: `ScopeCheckResult(status='needs_input', questions=questions, missing_fields=missing)`.


### backend/engine/workspace.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/backend/engine/workspace.py)


**Class `WorkspaceEvidenceRepository`** — bases: .


```python
WorkspaceEvidenceRepository.__init__(self, connection, context)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
WorkspaceEvidenceRepository.search_evidence(self, query, *, selected_document_version_ids=None, department_id=None)
```

Return expression: `[EvidenceChunk(chunk_id=str(row['chunk_id']), document_version_id=str(row['document_version_id']), title=row['title'], source_uri=row['source_uri'], locator=row['locator'], text=row['text'], content_hash=row['content_hash'], department_id=str(department), access_scope=row['access_status'], external_model_allowed=row['external_model_allowed']) for row in result['chunks']]`.


```python
WorkspaceEvidenceRepository.get_historical_costs(self, query, department_id)
```

Return expression: `[]`.


**Class `WorkspaceMockAdapter`** — bases: .

Deterministic, explicitly mock evidence preview with resolvable citations.


```python
WorkspaceMockAdapter.__init__(self)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
WorkspaceMockAdapter.generate(self, assignment, evidence, *, generation_context)
```

Return expression: `(report, UsageRecord(provider='mock', model='workspace-evidence-preview-v1', prompt_version='v2', input_units=sum((len(chunk.text.split()) for chunk in evidence)), output_units=sum((len(section['content'].split()) for section in sections))))`.


### evaluation/__init__.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/evaluation/__init__.py)

No named symbols; module-level setup/script code only.


### evaluation/retrieval_baseline.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/evaluation/retrieval_baseline.py)


```python
run_baseline(query_file: str | Path='evaluation/retrieval_queries.json') -> dict
```

Return expression: `{'answerable_top5': {'passed': answerable_passed, 'total': answerable_total, 'fraction': answerable_passed / answerable_total if answerable_total else 0.0}, 'all_behavior_checks': {'passed': behavior_passed, 'total': len(cases), 'fraction': behavior_passed / len(cases) if cases else 0.0}, 'results': results}`.


```python
main() -> int
```

Return expression: `0 if result['all_behavior_checks']['passed'] == result['all_behavior_checks']['total'] else 1`.


### scripts/demo_jai_week2.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/scripts/demo_jai_week2.py)


```python
load(name)
```

Return expression: `json.loads((FIX / name).read_text())`.


### scripts/demo_jai_week3.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/scripts/demo_jai_week3.py)

No named symbols; module-level setup/script code only.


### scripts/serve_week2.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/scripts/serve_week2.py)

No named symbols; module-level setup/script code only.


### tests/test_api.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/tests/test_api.py)


```python
no_database()
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
test_legacy_entry_point_uses_shared_app()
```

Checks legacy entry point uses shared app.


```python
test_health_and_authenticated_boundary()
```

Checks health and authenticated boundary.


```python
test_validation_rejects_legacy_source_keys_and_blank_problem()
```

Checks validation rejects legacy source keys and blank problem.


### tests/test_engine_week2.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/tests/test_engine_week2.py)


```python
load(name: str)
```

Return expression: `json.loads((FIX / name).read_text())`.


```python
test_12_query_retrieval_baseline_passes()
```

Checks 12 query retrieval baseline passes.


```python
test_unrelated_request_returns_evidence_gap_before_model_call()
```

Checks unrelated request returns evidence gap before model call.


```python
test_forbidden_chunk_never_enters_model_context()
```

Checks forbidden chunk never enters model context.


```python
test_context_is_ranked_limited_and_source_aware()
```

Checks context is ranked limited and source aware.


```python
test_first_chunk_cannot_exceed_context_budget()
```

Checks first chunk cannot exceed context budget.


### tests/test_engine_week3.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/tests/test_engine_week3.py)


```python
load(name: str)
```

Return expression: `json.loads((FIX / name).read_text())`.


```python
test_complete_source_backed_report_has_methodology_and_cost_range()
```

Checks complete source backed report has methodology and cost range.


```python
test_missing_cost_evidence_is_null_with_reason()
```

Checks missing cost evidence is null with reason.


```python
test_fake_citation_is_rejected()
```

Checks fake citation is rejected.


```python
test_evidence_map_covers_requested_sections_or_marks_gap()
```

Checks evidence map covers requested sections or marks gap.


### tests/test_week2.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/7d6562aa77b874a863ec9cf2bfd11d5392388f73/tests/test_week2.py)


```python
database(request)
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
metadata(**changes)
```

Return expression: `DocumentInput(**{**MANIFEST['pdf'], **changes})`.


```python
ingest(conn, content=PDF, **changes)
```

Return expression: `get_job(conn, job, CTX)`.


```python
assignment(**changes)
```

Return expression: `AssignmentInput(**{'problem': 'Improve permit intake', 'department_id': DEPT, 'intended_result': 'A preliminary improvement plan', **changes})`.


```python
test_money_repeat_and_scope(database)
```

Checks money repeat and scope.


```python
test_rejections_and_traceable_correction(database)
```

Checks rejections and traceable correction.


```python
test_collision_and_legitimate_equal_payments(database)
```

Checks collision and legitimate equal payments.


```python
test_invalid_money(database, replacement)
```

Checks invalid money.


```python
test_versions_and_page_search(database)
```

Checks versions and page search.


```python
test_failed_documents_have_no_evidence(database)
```

Checks failed documents have no evidence.


```python
test_assignments_and_authorization(database)
```

Checks assignments and authorization.


**Class `CaptureModel`** — bases: .


```python
CaptureModel.generate(self, assignment, evidence)
```

Return expression: `({'report_id': str(uuid4()), 'assignment_id': assignment.assignment_id, 'version': 1, 'status': 'draft', 'sections': [{'name': 'findings', 'content': 'Fixture response', 'citation_ids': []}], 'citations': []}, UsageRecord(provider='mock', model='capture', prompt_version='v1', input_units=0, output_units=0))`.


```python
test_engine_evidence_permissions_and_gap(database)
```

Checks engine evidence permissions and gap.


```python
client_for(database, **options)
```

Return expression: `TestClient(create_app(lambda: connect(database.info.dbname), context=CTX, token=TOKEN, local_mode=True, **options))`.


```python
test_api_persistence_upload_and_failures(database)
```

Checks api persistence upload and failures.


```python
test_api_cannot_self_approve_model_use(database)
```

Checks api cannot self approve model use.


```python
test_api_refuses_nonlocal_configuration()
```

Checks api refuses nonlocal configuration.


```python
test_exported_week2_contracts_match()
```

Checks exported week2 contracts match.


```python
test_interrupted_job_can_resume_and_unknown_access_is_hidden(database)
```

Checks interrupted job can resume and unknown access is hidden.


```python
test_chunk_budget_and_deduplication(database)
```

Checks chunk budget and deduplication.


```python
test_invalid_shared_ids_return_structured_engine_error(database)
```

Checks invalid shared ids return structured engine error.


```python
test_unapproved_readable_document_can_be_read_but_not_sent_externally(database)
```

Checks unapproved readable document can be read but not sent externally.


```python
test_changed_pdf_preserves_old_chunks(database)
```

Checks changed pdf preserves old chunks.


```python
test_same_job_concurrent_workers_create_one_version(database)
```

Checks same job concurrent workers create one version.


```python
test_same_job_concurrent_workers_create_one_version.work()
```

Return expression: `process_job(conn, identifier)`.


```python
test_engine_respects_assignment_department_even_if_actor_can_read_both(database)
```

Checks engine respects assignment department even if actor can read both.


```python
test_workspace_consult_uses_saved_assignment_and_database_citations(database)
```

Checks workspace consult uses saved assignment and database citations.


```python
test_workspace_consult_does_not_fall_back_to_fixtures(database)
```

Checks workspace consult does not fall back to fixtures.


```python
test_new_engine_repository_restricts_department(database)
```

Checks new engine repository restricts department.


## origin/jai-week2-3 — 2fdb258


### backend/engine/demo_retrieval.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2fdb25804a38542be6790c656ea0b0af1a8591ff/backend/engine/demo_retrieval.py)


**Class `RetrievalBundle`** — bases: .

- `evidence: list[EvidenceChunk]` — required.
- `trace: RetrievalTrace` — required.

```python
prepare_query(assignment: Assignment) -> str
```

Return expression: `' '.join((part.strip() for part in parts if part and part.strip()))`.


```python
_select_context(query: str, candidates: list[EvidenceChunk], access_context: AccessContext, *, selected_document_version_ids: list[str] | None=None, max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `RetrievalBundle(evidence=selected, trace=trace)`.


```python
retrieve_for_assignment(assignment: Assignment, repository: EvidenceRepository, access_context: AccessContext, *, max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `_select_context(query, candidates, access_context, selected_document_version_ids=assignment.selected_document_version_ids, max_chunks=max_chunks, max_context_words=max_context_words)`.


```python
retrieve_query(query: str, repository: EvidenceRepository, access_context: AccessContext, *, selected_document_version_ids: list[str] | None=None, department_id: str | None='dept-fixture-001', max_chunks: int=5, max_context_words: int=450) -> RetrievalBundle
```

Return expression: `_select_context(query, candidates, access_context, selected_document_version_ids=selected_document_version_ids, max_chunks=max_chunks, max_context_words=max_context_words)`.


### tests/test_engine_week2.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2fdb25804a38542be6790c656ea0b0af1a8591ff/tests/test_engine_week2.py)


```python
load(name: str)
```

Return expression: `json.loads((FIX / name).read_text())`.


```python
test_12_query_retrieval_baseline_passes()
```

Checks 12 query retrieval baseline passes.


```python
test_unrelated_request_returns_evidence_gap_before_model_call()
```

Checks unrelated request returns evidence gap before model call.


```python
test_forbidden_chunk_never_enters_model_context()
```

Checks forbidden chunk never enters model context.


```python
test_context_is_ranked_limited_and_source_aware()
```

Checks context is ranked limited and source aware.


## origin/yasha-week1 — 2176e8a


### backend/api/__init__.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2176e8abba2989c04e6019d485042920a9c6018b/backend/api/__init__.py)

No named symbols; module-level setup/script code only.


### backend/api/main.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2176e8abba2989c04e6019d485042920a9c6018b/backend/api/main.py)


```python
validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse
```

Map FastAPI/Pydantic failures to the stable Week 1 frontend error shape.


```python
health() -> dict[str, str]
```

Return expression: `{'status': 'ok', 'service': 'ai-corps-api', 'week': '1'}`.


```python
create_assignment(payload: AssignmentCreate) -> AssignmentResponse
```

Validate, normalize, assign a server ID, and store one assignment.


```python
get_assignment(assignment_id: str) -> AssignmentResponse
```

Return expression: `assignment`.


### backend/api/models.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2176e8abba2989c04e6019d485042920a9c6018b/backend/api/models.py)


**Class `AssignmentCreate`** — bases: `BaseModel`.

Fields accepted from the browser when creating a consulting assignment.

- `problem: str` — required.
- `department_id: str` — required.
- `intended_result: str` — required.
- `required_sections: list[str]` — `Field(min_length=1)`.
- `audience: str` — required.
- `constraints: list[str]` — `Field(default_factory=list)`.
- `selected_document_version_ids: list[str]` — `Field(default_factory=list)`.
- `request_type: Literal['problem', 'RFP', 'RFQ']` — `'problem'`.

```python
AssignmentCreate.reject_blank_text(cls, value: str) -> str
```

Return expression: `normalized`.


```python
AssignmentCreate.normalize_required_sections(cls, values: list[str]) -> list[str]
```

Return expression: `normalized`.


```python
AssignmentCreate.normalize_constraints(cls, values: list[str]) -> list[str]
```

Return expression: `[value.strip() for value in values if value.strip()]`.


**Class `AssignmentResponse`** — bases: `AssignmentCreate`.

Normalized assignment returned by the application API.

- `assignment_id: str` — required.
- `schema_version: Literal['1.0']` — `'1.0'`.
- `created_by: str` — required.

**Class `ErrorField`** — bases: `BaseModel`.

- `field: str` — required.
- `message: str` — required.

**Class `ErrorBody`** — bases: `BaseModel`.

- `code: str` — required.
- `message: str` — required.
- `fields: list[ErrorField]` — `Field(default_factory=list)`.

**Class `ErrorResponse`** — bases: `BaseModel`.

- `error: ErrorBody` — required.

### backend/api/repository.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2176e8abba2989c04e6019d485042920a9c6018b/backend/api/repository.py)


**Class `InMemoryAssignmentRepository`** — bases: .

Small fake repository used to make the workflow runnable before the DB is ready.

- `assignments: dict[str, AssignmentResponse]` — `field(default_factory=dict)`.

```python
InMemoryAssignmentRepository.create(self, assignment: AssignmentResponse) -> AssignmentResponse
```

Return expression: `assignment`.


```python
InMemoryAssignmentRepository.get(self, assignment_id: str) -> AssignmentResponse | None
```

Return expression: `self.assignments.get(assignment_id)`.


```python
InMemoryAssignmentRepository.clear(self) -> None
```

Test helper so each test begins with a known empty repository.


### tests/test_api.py

[Source at reviewed commit](https://github.com/jonathankarun/AICorp-1/blob/2176e8abba2989c04e6019d485042920a9c6018b/tests/test_api.py)


```python
setup_function() -> None
```

Initializes state or performs this module’s command/side effects; no explicit value returned.


```python
test_health_endpoint_returns_fixed_success() -> None
```

Checks health endpoint returns fixed success.


```python
test_valid_assignment_returns_id_and_normalized_data() -> None
```

Checks valid assignment returns id and normalized data.


```python
test_whitespace_problem_is_rejected_and_creates_nothing() -> None
```

Checks whitespace problem is rejected and creates nothing.


Frontend additions and inputs/outputs are described in [Branch additions](branches.md); complete typed frontend contracts are in the pinned branch source under `apps/web/src/types.ts`.
