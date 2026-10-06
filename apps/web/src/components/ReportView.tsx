import { useState } from "react";
import type { EvidenceChunk, Report } from "../types";

type Props = { report: Report; evidence: EvidenceChunk[] };

function labelFromName(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function ReportView({ report, evidence }: Props) {
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceChunk | null>(null);

  const citationById = Object.fromEntries(
    report.citations.map((citation) => [citation.citation_id, citation]),
  );
  const evidenceById = Object.fromEntries(
    evidence.map((chunk) => [chunk.chunk_id, chunk]),
  );

  return (
    <section className="card" aria-label="mock report">
      <div className="report-heading">
        <h2>4. Structured mock report</h2>
        <span className="badge">{report.status.toUpperCase()}</span>
      </div>
      <p className="muted">
        Report {report.report_id} · version {report.version}
      </p>

      {report.sections.map((section) => (
        <article key={section.name} className="report-section">
          <h3>{labelFromName(section.name)}</h3>
          <p>{section.content}</p>
          <div className="citation-row">
            {section.citation_ids.map((citationId) => {
              const citation = citationById[citationId];
              const chunk = citation ? evidenceById[citation.evidence_chunk_id] : undefined;
              if (!citation || !chunk) return null;
              return (
                <button
                  type="button"
                  className="link-button"
                  key={citationId}
                  onClick={() => setSelectedEvidence(chunk)}
                >
                  {citationId}: {chunk.locator}
                </button>
              );
            })}
          </div>
        </article>
      ))}

      <p className="muted">Local mock evidence preview. No live model was called; source excerpts are not recommendations.</p>
      {report.cost_evidence && <section aria-label="cost evidence">
        <h3>Historical cost evidence</h3>
        <p>{report.cost_evidence.min_amount === null
          ? report.cost_evidence.reason
          : `${report.cost_evidence.min_amount}–${report.cost_evidence.max_amount} ${report.cost_evidence.currency}`}</p>
        <p>{report.cost_evidence.limitation}</p>
      </section>}
      <h3>Assumptions</h3>
      <ul>{report.assumptions.map((item) => <li key={item}>{item}</li>)}</ul>

      <h3>Missing information</h3>
      <ul>{report.missing_information.map((item) => <li key={item}>{item}</li>)}</ul>

      <h3>Expert review needed</h3>
      <ul>{report.expert_review_needed.map((item) => <li key={item}>{item}</li>)}</ul>

      {selectedEvidence && (
        <aside className="source-details" aria-label="source details">
          <h3>Source details</h3>
          <strong>{selectedEvidence.title}</strong>
          <p>Evidence ID: {selectedEvidence.chunk_id}</p>
          <p>Document version: {selectedEvidence.document_version_id}</p>
          <p>Locator: {selectedEvidence.locator}</p>
          <p>{selectedEvidence.text}</p>
          <code>{selectedEvidence.source_uri}</code>
        </aside>
      )}
    </section>
  );
}
