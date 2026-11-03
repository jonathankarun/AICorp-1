import { useEffect, useRef, useState } from 'react';

type Api = (path: string, options?: RequestInit) => Promise<any>;
const stages = ['Ingest the PDF', 'Store and read the assignment', 'Retrieve evidence', 'Display the original source', 'Calculate spending', 'Record a sample correction'];

const explanations = [
  {
    process: 'The backend reads the bundled PDF, checks its format and size, and creates an ingestion job. It preserves the original bytes and a content hash, extracts readable text page by page, and splits it into chunks of up to 1,200 characters without crossing page boundaries. Each chunk keeps its page number and document version. The job becomes ready after extraction succeeds.',
    purpose: 'A PDF becomes searchable text while retaining a route back to its original source. The passages below are extracted from the file, not written by an AI. Image-only pages need OCR, which this subsystem does not provide.',
  },
  {
    process: 'The backend checks department access and confirms the selected source is ready and allowed. It inserts the problem, intended result, and selected document version into PostgreSQL, assigns an ID, and reads the assignment back using that ID.',
    purpose: 'The consulting task is tied to a specific source version. Uploading a newer version does not silently change the evidence chosen for this assignment. This run proves database write/read-back inside a temporary transaction; it does not retain this demo assignment afterward.',
  },
  {
    process: 'The backend searches for “timeline” using PostgreSQL full-text keyword matching. It filters for the allowed department, ready and unblocked sources, and the selected document version before ranking matches. Results include the passage, document title, version ID, and page locator.',
    purpose: 'The engine can receive relevant evidence with traceable references instead of an entire unfiltered document collection. “Six weeks” comes from the source passage. This step retrieves evidence; it does not generate advice or perform semantic/vector search.',
  },
  {
    process: 'The backend checks access again and retrieves the stored original PDF bytes for the matching document version. The browser displays that PDF starting at page 1, where the timeline passage appears.',
    purpose: 'Someone can compare the search result with its original context. This establishes traceability, not that the document is factually correct or that a reviewer has approved it. The demo displays the source without making you submit a review.',
  },
  {
    process: 'The backend reads five CSV rows, validates payment fields, matches vendor and department records, and imports them under a unique demo source key. It sums decimal amounts by classification for the October source population and compares consulting spending with the matching $10,000 budget.',
    purpose: 'Consulting is $100 + $200 − $20 = $280; operational is $500; unresolved is $50. The share is $280 ÷ $10,000 × 100 = 2.80%. Refunds reduce spending, and uncertain classifications remain separate rather than being counted as consulting.',
  },
  {
    process: 'A scripted fictional decision requests changing the sample $50 from unresolved to consulting. The correction service checks the actor’s reviewer permission and expected old classification, records the old/new categories, actor, reason, and time, then updates the payment and recalculates totals.',
    purpose: 'Consulting becomes $330, unresolved becomes $0, operational stays $500, and the share becomes 3.30%. The overall $830 total does not change: this is a reclassification, not a new payment. The audit explains the change. This scripted decision is not an inference from the PDF or a human approval.',
  },
];

export function GuidedDemo({ api }: { api: Api }) {
  const [result, setResult] = useState<any>(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pdf, setPdf] = useState('');
  const running = useRef(false);
  useEffect(() => {
    if (!result) return;
    const bytes = Uint8Array.from(atob(result.pdf_base64), c => c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
    setPdf(url);
    return () => URL.revokeObjectURL(url);
  }, [result]);
  async function run() {
    if (running.current) return;
    running.current = true;
    setBusy(true); setError(''); setResult(null); setPdf(''); setStep(0);
    try { setResult(await api('/demo/run', { method: 'POST' })); }
    catch (e) { setError((e as Error).message); }
    finally { running.current = false; setBusy(false); }
  }
  return <section className="guided-demo" aria-labelledby="guided-title">
    <p className="eyebrow">GUIDED CAPSTONE DEMO</p>
    <h2 id="guided-title">Watch the data subsystem at work</h2>
    <p>One click runs a fictional PDF and payment CSV through the real backend. No uploads or form filling needed.</p>
    <p className="muted">Temporary database records are discarded after the run. The stages below display its captured results; your saved workspace stays unchanged. No AI model is called.</p>
    <div className="demo-controls">
      <button disabled={busy} onClick={run}>{busy ? 'Running the real pipeline…' : result ? 'Run demo again' : 'Run demo'}</button>
      <p>Take your time: steps change only when you click Next, Previous, or a stage above the results.</p>
    </div>
    {error && <p role="alert">Demo failed: {error}. Try running it again.</p>}
    {result && <>
      <p className="muted">Backend run complete. Showing result {step + 1} of {stages.length}. {step === stages.length - 1 ? 'Walkthrough complete — replay any stage or run again.' : ''}</p>
      <nav className="demo-stage-tabs" aria-label="Demo stages">{stages.map((name, index) => <button key={name} aria-current={step === index ? 'step' : undefined} onClick={() => { setStep(index); }}>{index + 1}. {name}</button>)}</nav>
      <div className="demo-result" aria-live="polite">
        <h3>{step + 1}. {stages[step]}</h3>
        <p><strong>What happens:</strong> {explanations[step].process}</p>
        <p><strong>Why it matters:</strong> {explanations[step].purpose}</p>
        {step === 0 && <><p>The PDF was validated, its original bytes stored, and its text split into page-linked chunks.</p><p><strong>Processing status: {result.job.status} · {result.extracted.length} chunks extracted</strong></p>{result.extracted.map((c: any, i: number) => <blockquote key={i}><strong>Page {c.page_number}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 1 && <><p>The assignment was inserted into PostgreSQL and read back using its ID within the temporary transaction.</p><p><strong>Problem:</strong> {result.assignment.problem}</p><p><strong>Intended result:</strong> {result.assignment.intended_result}</p><p><strong>Pinned source versions:</strong> {result.assignment.selected_document_version_ids.length}</p><p className="demo-id">Assignment ID: {result.assignment.assignment_id}</p><p>The demo discards this assignment afterward. The manual workspace can save assignments permanently.</p></>}
        {step === 2 && <><p>Query: <strong>timeline</strong>. The search checks source access and searches only the assigned document version.</p>{result.evidence.chunks.map((c: any) => <blockquote key={c.chunk_id}><strong>{c.title} · {c.locator}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 3 && <><p>The backend retrieved the original stored PDF. Compare page 1 with the retrieved “six weeks” passage. Displaying a source does not constitute a human review.</p>{pdf && <><a href={pdf} target="_blank" rel="noreferrer">Open sample PDF in a new tab</a><iframe title="Guided demo original PDF" src={pdf + '#page=1'} /></>}</>}
        {step === 4 && <><p>Imported {result.imported.inserted} CSV payments. The consulting total includes a −$20 refund.</p><Money value={result.before} /></>}
        {step === 5 && <><p>A scripted sample decision changes the unresolved $50 to consulting. The real correction service writes an audit entry.</p><p><strong>Consulting: ${result.before.consulting} → ${result.after.consulting}</strong></p><Money value={result.after} />{result.audit.map((a: any) => <blockquote key={a.audit_id}><strong>{a.old_value.classification} → {a.new_value.classification}</strong><p>{a.reason}</p><small>{a.created_at} · actor {a.actor_id}</small></blockquote>)}<p>All temporary records, including this correction, were discarded. Run again for the same starting totals.</p></>}
      </div>
      <div className="demo-controls">
        <button disabled={step === 0} onClick={() => { setStep(s => s - 1); }}>Previous</button>
        <button disabled={step === stages.length - 1} onClick={() => { setStep(s => s + 1); }}>Next</button>
      </div>
    </>}
  </section>;
}

function Money({ value }: { value: any }) {
  return <div className="demo-money"><p><strong>Consulting: ${value.consulting}</strong></p><p>Operational: ${value.operational}</p><p>Unresolved: ${value.unresolved}</p><p>{value.consulting_share_percent}% of the ${value.budget} October budget</p></div>;
}
