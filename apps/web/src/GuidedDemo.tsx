import { useEffect, useRef, useState } from 'react';

type Api = (path: string, options?: RequestInit) => Promise<any>;
const stages = ['Ingest the PDF', 'Store and read the assignment', 'Retrieve evidence', 'Display the original source', 'Calculate spending', 'Record a sample correction'];

const explanations = [
  {
    process: 'Extract PDF text into page-linked chunks and preserve the original file.',
    tools: 'Python · pypdf · SHA-256 hashing · chunks up to 1,200 characters · document versioning',
  },
  {
    process: 'Save the assignment with its selected source version, then read it back by ID.',
    tools: 'PostgreSQL · Psycopg · SQL transactions · access checks · version references',
  },
  {
    process: 'Search “timeline” in the selected source and return matching passages with page references.',
    tools: 'PostgreSQL full-text search · keyword matching · access filters · relevance ranking',
  },
  {
    process: 'Retrieve the stored PDF and display page 1 beside the source reference.',
    tools: 'Access checks · stored PDF bytes · browser Blob URL · PDF viewer',
  },
  {
    process: 'Import five payments and total October spending by category, including the refund.',
    tools: 'Python CSV parser · field validation · identity matching · decimal arithmetic · SQL aggregation',
  },
  {
    process: 'Reclassify the sample $50 as consulting and record the change. This is a scripted decision.',
    tools: 'Reviewer permissions · expected-value check · row lock · SQL transaction · audit log',
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
    <h2 id="guided-title">Data subsystem demo</h2>
    <p>Run the sample PDF and CSV workflow, then explore each result.</p>
    <p className="muted">Fictional data · Real backend results · Temporary records discarded · No AI calls</p>
    <div className="demo-controls">
      <button disabled={busy} onClick={run}>{busy ? 'Running the real pipeline…' : result ? 'Run demo again' : 'Run demo'}</button>
      <p>Use Next or Previous. No autoplay.</p>
    </div>
    {error && <p role="alert">Demo failed: {error}. Try running it again.</p>}
    {result && <>
      <p className="muted">Step {step + 1} of {stages.length} · Run complete</p>
      <nav className="demo-stage-tabs" aria-label="Demo stages">{stages.map((name, index) => <button key={name} aria-current={step === index ? 'step' : undefined} onClick={() => { setStep(index); }}>{index + 1}. {name}</button>)}</nav>
      <div className="demo-result" aria-live="polite">
        <h3>{step + 1}. {stages[step]}</h3>
        <p><strong>What happens:</strong> {explanations[step].process}</p>
        <p><strong>Tools &amp; methods:</strong> {explanations[step].tools}</p>
        {step === 0 && <><p><strong>Processing status: {result.job.status} · {result.extracted.length} chunks extracted</strong></p>{result.extracted.map((c: any, i: number) => <blockquote key={i}><strong>Page {c.page_number}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 1 && <><p><strong>Problem:</strong> {result.assignment.problem}</p><p><strong>Intended result:</strong> {result.assignment.intended_result}</p><p><strong>Pinned source versions:</strong> {result.assignment.selected_document_version_ids.length}</p><p className="demo-id">Assignment ID: {result.assignment.assignment_id}</p></>}
        {step === 2 && <><p>Query: <strong>timeline</strong></p>{result.evidence.chunks.map((c: any) => <blockquote key={c.chunk_id}><strong>{c.title} · {c.locator}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 3 && <><p>Page 1: “six weeks”. Source display only; no review recorded.</p>{pdf && <><a href={pdf} target="_blank" rel="noreferrer">Open sample PDF in a new tab</a><iframe title="Guided demo original PDF" src={pdf + '#page=1'} /></>}</>}
        {step === 4 && <><p>Imported {result.imported.inserted} CSV payments. The consulting total includes a −$20 refund.</p><Money value={result.before} /></>}
        {step === 5 && <><p><strong>Consulting: ${result.before.consulting} → ${result.after.consulting}</strong></p><Money value={result.after} />{result.audit.map((a: any) => <blockquote key={a.audit_id}><strong>{a.old_value.classification} → {a.new_value.classification}</strong><p>{a.reason}</p><small>{a.created_at} · actor {a.actor_id}</small></blockquote>)}</>}
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
