// this is the small demo for my data subsystem
// the numbers and source text here come from the database, nothing is made up in the browser
import { useState, type FormEvent } from 'react';
type Api = (path: string, options?: RequestInit) => Promise<any>;
const post = (body: unknown) => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export function DataDemo({ api }: { api: Api }) {
  const [money, setMoney] = useState<any>(null);
  const [cases, setCases] = useState<any[] | null>(null);
  const [topic, setTopic] = useState('process');
  const [reason, setReason] = useState('Reviewed the fictional payment evidence; this was consulting work.');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage('');
    try { await action(); } catch (error) { setMessage((error as Error).message); }
    finally { setBusy(false); }
  }
  async function compare(event: FormEvent) {
    event.preventDefault();
    await run(async () => setCases(await api('/comparables', post({ topic: topic.trim() || null, for_external_model: false }))));
  }
  return <section className="data-demo">
    <h2>Data subsystem demo</h2>
    <p>Try the fictional spending example, look up past work, then upload or search source evidence below.</p>
    {message && <p role="alert">{message}</p>}
    <h3>Spending and correction history</h3>
    <button disabled={busy} onClick={() => run(async () => setMoney(await api('/demo/spending')))}>Load spending</button>
    {money && <>
      <p><strong>Consulting: ${money.totals.consulting}</strong> · Operational: ${money.totals.operational} · Unresolved: ${money.totals.unresolved}</p>
      <p>{money.totals.consulting_share_percent}% of the ${money.totals.budget} budget. USD, October 2026, fictional payment export only.</p>
      <ul>{money.payments.map((p: any) => <li key={p.payment_id}>{p.source_key}: ${p.amount} — {p.classification}</li>)}</ul>
      <label>Reason for correction<input value={reason} onChange={e => setReason(e.target.value)} /></label>
      <button disabled={busy || !reason.trim() || !money.payments.some((p: any) => p.classification === 'unresolved')}
        onClick={() => run(async () => {
          const payment = money.payments.find((p: any) => p.classification === 'unresolved');
          await api(`/payments/${payment.payment_id}/classification`, post({ expected_classification: 'unresolved', classification: 'consulting', reason }));
          setMoney(await api('/demo/spending'));
        })}>Classify the unresolved $50 as consulting</button>
      <p>The base fixture starts at $280. This correction makes it $330 and records who changed it and why.</p>
      <h4>Saved corrections</h4>
      {money.audit.length === 0 ? <p>No corrections yet.</p> : <ul>{money.audit.map((a: any) => <li key={a.audit_id}>{a.old_value.classification} → {a.new_value.classification}: {a.reason} <small>{a.created_at} · actor {a.actor_id}</small></li>)}</ul>}
    </>}
    <h3>Find comparable past work</h3>
    <form onSubmit={compare}><label>Topic<input value={topic} onChange={e => setTopic(e.target.value)} /></label><button disabled={busy}>Find past work</button></form>
    {cases?.length === 0 && <p>No matching projects. Try “process”.</p>}
    {cases?.map(c => <article key={c.engagement_id}>
      <h4>{c.title}</h4><p>{c.vendor_name} · {c.match_reasons.join(', ')}</p>
      <p>Recorded payments: {c.payments.map((p: any) => `${p.currency} ${p.amount} (${p.transaction_count} payments)`).join(', ') || 'No payments recorded'}</p>
      <p>These are all recorded engagement payments; the spending example above uses a separate fiscal-period population.</p>
      <ul>{c.facts.map((f: any) => <li key={f.fact_id}>{f.kind}: {f.value ?? `Unknown — ${f.unknown_reason}`} (page {f.page_number})</li>)}</ul>
    </article>)}
  </section>;
}
