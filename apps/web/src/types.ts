// Browser types mirror the current Week 1 API/engine handoff shape.

export type AssignmentCreate = {
  problem: string;
  department_id: string;
  intended_result: string;
  required_sections: string[];
  audience: string;
  constraints: string[];
  selected_document_version_ids: string[];
  request_type: "problem" | "RFP" | "RFQ";
};

export type AssignmentResponse = AssignmentCreate & {
  assignment_id: string;
  schema_version: "1.0";
  created_by: string;
};

export type EvidenceChunk = {
  chunk_id: string;
  document_version_id: string;
  title: string;
  source_uri: string;
  locator: string;
  text: string;
  access_scope: string;
  external_model_allowed: boolean;
};

export type Citation = {
  citation_id: string;
  evidence_chunk_id: string;
};

export type ReportSection = {
  name: string;
  content: string;
  citation_ids: string[];
};

export type Report = {
  report_id: string;
  assignment_id: string;
  version: number;
  status: "draft" | "reviewed" | "approved";
  sections: ReportSection[];
  citations: Citation[];
  assumptions: string[];
  missing_information: string[];
  expert_review_needed: string[];
};
