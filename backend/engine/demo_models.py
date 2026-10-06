from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class Assignment(BaseModel):
    assignment_id: str
    schema_version: str = "1.0"
    problem: str
    department_id: str | None = None
    intended_result: str | None = None
    topic: str | None = None
    required_sections: list[str] = Field(default_factory=list)
    audience: str | None = None
    constraints: list[str] = Field(default_factory=list)
    selected_document_version_ids: list[str] = Field(default_factory=list)
    request_type: Literal["problem", "RFP", "RFQ"] = "problem"

    @field_validator("problem")
    @classmethod
    def problem_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("problem must not be blank")
        return value.strip()


class AccessContext(BaseModel):
    """Synthetic server-derived access context used by the engine demo."""

    actor_id: str = "demo-user"
    readable_scopes: list[str] = Field(default_factory=lambda: ["fixture", "public"])
    external_model_use: bool = True


class EvidenceChunk(BaseModel):
    chunk_id: str
    document_version_id: str
    title: str
    source_uri: str
    locator: str
    text: str
    content_hash: str | None = None
    department_id: str | None = None
    access_scope: str = "fixture"
    external_model_allowed: bool = True


class HistoricalCostRecord(BaseModel):
    record_id: str
    amount: str
    currency: str = "USD"
    fiscal_period: str
    amount_type: Literal["actual_payment", "contract_value", "estimate"] = "actual_payment"
    source_ids: list[str]


class CostEvidence(BaseModel):
    min_amount: str | None = None
    max_amount: str | None = None
    currency: str = "USD"
    fiscal_period: str | None = None
    amount_type: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    reason: str | None = None
    limitation: str | None = None


class Citation(BaseModel):
    citation_id: str
    evidence_chunk_id: str


class ReportSection(BaseModel):
    name: str
    content: str
    citation_ids: list[str] = Field(default_factory=list)


class Report(BaseModel):
    report_id: str
    assignment_id: str
    version: int = 1
    status: Literal["draft", "reviewed", "approved"] = "draft"
    sections: list[ReportSection]
    citations: list[Citation]
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    expert_review_needed: list[str] = Field(default_factory=list)
    cost_evidence: CostEvidence | None = None
    run_id: str | None = None

    @model_validator(mode="after")
    def validate_citation_references(self):
        citation_ids = {c.citation_id for c in self.citations}
        for section in self.sections:
            missing = set(section.citation_ids) - citation_ids
            if missing:
                raise ValueError(
                    f"section '{section.name}' references unknown citation IDs: {sorted(missing)}"
                )
        return self


class ScopeCheckResult(BaseModel):
    status: Literal["ready", "needs_input"]
    questions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class UsageRecord(BaseModel):
    provider: str
    model: str
    prompt_version: str
    input_units: int = 0
    output_units: int = 0
    elapsed_ms: int = 0
    mock: bool = True


class RetrievalTrace(BaseModel):
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    candidate_chunk_ids: list[str] = Field(default_factory=list)
    selected_chunk_ids: list[str] = Field(default_factory=list)
    rejected_chunk_ids: list[str] = Field(default_factory=list)
    selected_document_version_ids: list[str] = Field(default_factory=list)
    context_word_count: int = 0
    max_chunks: int = 5
    max_context_words: int = 450


class EvidenceMapEntry(BaseModel):
    section: str
    supporting_chunk_ids: list[str] = Field(default_factory=list)
    gap: bool = False
    notes: str | None = None


class EngineSuccess(BaseModel):
    result_type: Literal["report"] = "report"
    report: Report
    usage: UsageRecord
    retrieval_trace: RetrievalTrace | None = None
    evidence_map: list[EvidenceMapEntry] = Field(default_factory=list)
    methodology_stages: list[str] = Field(default_factory=list)


class EngineNeedsInput(BaseModel):
    result_type: Literal["needs_input"] = "needs_input"
    assignment_id: str
    questions: list[str]
    missing_fields: list[str]
    model_calls: int = 0


class EngineEvidenceGap(BaseModel):
    result_type: Literal["evidence_gap"] = "evidence_gap"
    assignment_id: str
    message: str
    query: str
    rejected_chunk_ids: list[str] = Field(default_factory=list)
    model_calls: int = 0


class EngineFailure(BaseModel):
    result_type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool = False


EngineResult = EngineSuccess | EngineNeedsInput | EngineEvidenceGap | EngineFailure
