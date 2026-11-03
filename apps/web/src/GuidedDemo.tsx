import { useEffect, useRef, useState } from 'react';

type Api = (path: string, options?: RequestInit) => Promise<any>;
const stages = ['Ingest the PDF', 'Store and read the assignment', 'Retrieve evidence', 'Display the original source', 'Calculate spending', 'Record a sample correction'];

export function GuidedDemo({ api }: { api: Api }) {
  const [result, setResult] = useState<any>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);
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
  useEffect(() => {
    if (!result || !playing || step === stages.length - 1) return;
    const timer = setTimeout(() => setStep(s => s + 1), 6000);
    return () => clearTimeout(timer);
  }, [result, playing, step]);
  async function run() {
    if (running.current) return;
    running.current = true;
    setBusy(true); setError(''); setResult(null); setPdf(''); setStep(0);
    try { setResult(await api('/demo/run', { method: 'POST' })); }
    catch (e) { setError((e as Error).message); }
    finally { running.current = false; setBusy(false); }
  }
  return <section className="guided-demo" aria-labelledby="guided-title">
    <p className="eyebrow">AUTOMATIC CAPSTONE DEMO</p>
    <h2 id="guided-title">Watch the data subsystem at work</h2>
    <p>One click runs a fictional PDF and payment CSV through the real backend. No uploads or form filling needed.</p>
    <p className="muted">Temporary database records are discarded after the run. The stages below display its captured results; your saved workspace stays unchanged. No AI model is called.</p>
    <div className="demo-controls">
      <button disabled={busy} onClick={run}>{busy ? 'Running the real pipeline…' : result ? 'Run demo again' : 'Run demo'}</button>
      <label className="check"><input type="checkbox" checked={playing} onChange={e => setPlaying(e.target.checked)} />Advance automatically every 6 seconds</label>
    </div>
    {error && <p role="alert">Demo failed: {error}. Try running it again.</p>}
    {result && <>
      <p className="muted">Backend run complete. Showing result {step + 1} of {stages.length}. {step === stages.length - 1 ? 'Walkthrough complete — replay any stage or run again.' : ''}</p>
      <nav className="demo-stage-tabs" aria-label="Demo stages">{stages.map((name, index) => <button key={name} aria-current={step === index ? 'step' : undefined} onClick={() => { setStep(index); setPlaying(false); }}>{index + 1}. {name}</button>)}</nav>
      <div className="demo-result" aria-live="polite">
        <h3>{step + 1}. {stages[step]}</h3>
        {step === 0 && <><p>The PDF was validated, its original bytes stored, and its text split into page-linked chunks.</p><p><strong>Processing status: {result.job.status} · {result.extracted.length} chunks extracted</strong></p>{result.extracted.map((c: any, i: number) => <blockquote key={i}><strong>Page {c.page_number}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 1 && <><p>The assignment was inserted into PostgreSQL and read back using its ID within the temporary transaction.</p><p><strong>Problem:</strong> {result.assignment.problem}</p><p><strong>Intended result:</strong> {result.assignment.intended_result}</p><p><strong>Pinned source versions:</strong> {result.assignment.selected_document_version_ids.length}</p><p className="demo-id">Assignment ID: {result.assignment.assignment_id}</p><p>The demo discards this assignment afterward. The manual workspace can save assignments permanently.</p></>}
        {step === 2 && <><p>Query: <strong>timeline</strong>. The search checks source access and searches only the assigned document version.</p>{result.evidence.chunks.map((c: any) => <blockquote key={c.chunk_id}><strong>{c.title} · {c.locator}</strong><p>{c.text}</p></blockquote>)}</>}
        {step === 3 && <><p>The backend retrieved the original stored PDF. Compare page 1 with the retrieved “six weeks” passage. Displaying a source does not constitute a human review.</p>{pdf && <><a href={pdf} target="_blank" rel="noreferrer">Open sample PDF in a new tab</a><iframe title="Guided demo original PDF" src={pdf + '#page=1'} /></>}</>}
        {step === 4 && <><p>Imported {result.imported.inserted} CSV payments. The consulting total includes a −$20 refund.</p><Money value={result.before} /></>}
        {step === 5 && <><p>A scripted sample decision changes the unresolved $50 to consulting. The real correction service writes an audit entry.</p><p><strong>Consulting: ${result.before.consulting} → ${result.after.consulting}</strong></p><Money value={result.after} />{result.audit.map((a: any) => <blockquote key={a.audit_id}><strong>{a.old_value.classification} → {a.new_value.classification}</strong><p>{a.reason}</p><small>{a.created_at} · actor {a.actor_id}</small></blockquote>)}<p>All temporary records, including this correction, were discarded. Run again for the same starting totals.</p></>}
      </div>
      <div className="demo-controls">
        <button disabled={step === 0} onClick={() => { setPlaying(false); setStep(s => s - 1); }}>Previous</button>
        <button disabled={step === stages.length - 1} onClick={() => { setPlaying(false); setStep(s => s + 1); }}>Next</button>
      </div>
    </>}
  </section>;
}

function Money({ value }: { value: any }) {
  return <div className="demo-money"><p><strong>Consulting: ${value.consulting}</strong></p><p>Operational: ${value.operational}</p><p>Unresolved: ${value.unresolved}</p><p>{value.consulting_share_percent}% of the ${value.budget} October budget</p></div>;
}
