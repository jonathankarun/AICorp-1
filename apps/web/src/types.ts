// Shared workspace and Jai report boundary; IDs are database UUID strings.

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
  schema_version: "2.0";
  created_at: string;
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
  cost_evidence?: { min_amount: string | null; max_amount: string | null; currency: string; reason: string | null; limitation: string | null } | null;
};

export type ConsultationResult =
  | { result_type: "report"; report: Report; evidence: EvidenceChunk[] }
  | { result_type: "needs_input"; questions: string[] }
  | { result_type: "evidence_gap"; message: string }
  | { result_type: "error"; message: string };
