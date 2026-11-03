import { useEffect, useRef, useState } from 'react';

type Check = { name: string; status: 'PASS' | 'FAIL' | 'ERROR' | 'SKIP'; expected: unknown; actual: unknown };
type Report = { run_id: string; completed_at: string; duration_ms: number; status: string; passed: number; total: number; checks: Check[]; scope: string };
type Api = (path: string, options?: RequestInit) => Promise<any>;
function display(value: unknown): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (value === null || value === undefined) return 'Missing';
  if (Array.isArray(value)) return value.map(display).join(', ') || 'None';
  if (typeof value === 'object') return Object.entries(value).map(([key, item]) =>
    `${key.replaceAll('_', ' ')}: ${display(item)}`).join('\n');
  return String(value);
}

export function Validation({ api }: { api: Api }) {
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [download, setDownload] = useState('');
  const running = useRef(false);
  useEffect(() => {
    if (!report) { setDownload(''); return; }
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    setDownload(url);
    return () => URL.revokeObjectURL(url);
  }, [report]);
  async function run() {
    if (running.current) return;
    running.current = true; setBusy(true); setError(''); setReport(null);
    try { setReport(await api('/demo/validate', { method: 'POST' })); }
    catch (e) { setError((e as Error).message); }
    finally { running.current = false; setBusy(false); }
  }
  return <section className="validation" aria-labelledby="validation-title">
    <h2 id="validation-title">Validate the subsystem</h2>
    <p>Run real checks for documents, retrieval, payments, permissions, and repeatability.</p>
    <p className="muted">Uses fictional fixtures and temporary database records. Results cover these checks, not every possible case.</p>
    <div className="demo-controls">
      <button disabled={busy} onClick={run}>{busy ? 'Running validation…' : 'Run validation'}</button>
      {report && download && <a href={download} download={`subsystem-validation-${report.run_id}.json`}>Download report</a>}
    </div>
    {error && <p role="alert" className="error">Validation could not complete: {error}. Retry when the service is available.</p>}
    {report && <>
      <p role="status" className="validation-summary"><strong>{report.status} — {report.passed}/{report.total} checks passed</strong></p>
      <p className="muted">Completed {new Date(report.completed_at).toLocaleString()} · {(report.duration_ms / 1000).toFixed(2)} seconds</p>
      <div className="validation-checks">{report.checks.map((check, index) => <section className="validation-check" key={index}>
        <div className="validation-check-heading"><h3>{check.name}</h3><strong className={`check-status ${check.status === 'PASS' ? '' : 'check-attention'}`}>{check.status}</strong></div>
        <dl><div><dt>Expected</dt><dd><pre>{display(check.expected)}</pre></dd></div><div><dt>Actual</dt><dd><pre>{display(check.actual)}</pre></dd></div></dl>
      </section>)}</div>
      <p className="muted">{report.scope}</p>
    </>}
  </section>;
}
