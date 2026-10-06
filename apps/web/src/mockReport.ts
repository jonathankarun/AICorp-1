import type { EvidenceChunk, Report } from "./types";

// Mirrors Jai's committed Week 1 mock report shape instead of defining a second
// incompatible Report contract in the frontend.
export const MOCK_REPORT: Report = {
  report_id: "report-fixture-001",
  assignment_id: "assignment-fixture-001",
  version: 1,
  status: "draft",
  sections: [
    {
      name: "problem_summary",
      content:
        "The fictional department needs a more consistent intake process and a preliminary improvement plan.",
      citation_ids: ["cite-001"],
    },
    {
      name: "findings",
      content:
        "The fixture establishes a six-week horizon and asks for a structured improvement deliverable.",
      citation_ids: ["cite-001", "cite-002"],
    },
    {
      name: "alternatives",
      content:
        "Alternative A standardizes intake with a checklist. Alternative B adds a triage step before assignment.",
      citation_ids: [],
    },
    {
      name: "recommendation",
      content:
        "Pilot a standardized intake checklist first, then add triage if the pilot shows unresolved routing delays.",
      citation_ids: [],
    },
    {
      name: "implementation_steps",
      content:
        "Week 1 map the process; Week 2 draft the checklist; Weeks 3-4 pilot; Week 5 measure results; Week 6 revise and document.",
      citation_ids: ["cite-001"],
    },
    {
      name: "risks",
      content:
        "Risks include low adoption, unclear ownership, and overfitting the process to the synthetic fixture.",
      citation_ids: [],
    },
  ],
  citations: [
    { citation_id: "cite-001", evidence_chunk_id: "chunk-fixture-001" },
    { citation_id: "cite-002", evidence_chunk_id: "chunk-fixture-002" },
  ],
  assumptions: ["Synthetic fixture only", "No live City data", "No live model API"],
  missing_information: [
    "Real staffing levels",
    "Observed baseline cycle time",
    "Approved budget evidence",
  ],
  expert_review_needed: [
    "Operational feasibility",
    "Department-specific workflow",
    "Any future procurement implications",
  ],
};

// Source details mirror Jai's current backend.engine.repository fixture evidence.
export const MOCK_EVIDENCE: EvidenceChunk[] = [
  {
    chunk_id: "chunk-fixture-001",
    document_version_id: "doc-fixture-v1",
    title: "Fictional Process Improvement Project",
    source_uri: "fixture://process-improvement/page-1",
    locator: "page 1",
    text: "The fictional department requests a preliminary improvement plan with a six-week implementation timeline.",
    access_scope: "fixture",
    external_model_allowed: true,
  },
  {
    chunk_id: "chunk-fixture-002",
    document_version_id: "doc-fixture-v1",
    title: "Fictional Process Improvement Project",
    source_uri: "fixture://process-improvement/page-2",
    locator: "page 2",
    text: "Requested deliverables include findings, alternatives, an implementation plan, risks, and measures of success.",
    access_scope: "fixture",
    external_model_allowed: true,
  },
];
