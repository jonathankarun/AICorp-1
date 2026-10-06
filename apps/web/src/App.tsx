import { useEffect, useState, type FormEvent } from "react";
import { ReportView } from "./components/ReportView";
import { AssignmentForm } from "./components/AssignmentForm";
import type { ConsultationResult } from "./types";
import "./style.css";
import { apiRequest, guidance } from "./api";

export type Document = {
  document_version_id: string;
  title: string;
  version: number;
  external_model_allowed: boolean;
};
type Job = {
  job_id: string;
  title: string;
  status: string;
  error_code: string | null;
  size_bytes: number;
};
type Chunk = { chunk_id: string; title: string; locator: string; text: string };
export type Assignment = {
  problem: string;
  department_id: string;
  intended_result: string;
  audience: string;
  constraints: string[];
  required_sections: string[];
  selected_document_version_ids: string[];
  request_type: "problem" | "RFP" | "RFQ";
  assignment_id?: string;
};
const initial: Assignment = {
  request_type: "problem",
  problem: "",
  department_id: "10000000-0000-4000-8000-000000000001",
  intended_result: "",
  audience: "Department leadership",
  constraints: [],
  required_sections: ["problem_summary", "findings", "recommendation", "implementation_steps"],
  selected_document_version_ids: [],
};
export default function App() {
  const [token, setToken] = useState(sessionStorage.getItem("demoToken") || "");
  const [connected, setConnected] = useState(false);
  const [form, setForm] = useState<Assignment>(initial);
  const [docs, setDocs] = useState<Document[]>([]),
    [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [consultation, setConsultation] = useState<ConsultationResult | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false),
    [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState(""),
    [chunks, setChunks] = useState<Chunk[]>([]),
    [searched, setSearched] = useState(false);
  async function api(path: string, options: RequestInit = {}) {
    return apiRequest(token, path, options);
  }
  async function refresh() {
    const [sources, uploads] = await Promise.all([
      api("/documents"),
      api("/uploads"),
    ]);
    setDocs(sources);
    setJobs(uploads);
  }
  async function connect() {
    setError("");
    setConsultation(null);
    try {
      await refresh();
      sessionStorage.setItem("demoToken", token);
      setConnected(true);
      const saved = localStorage.getItem("assignmentId");
      if (saved) {
        const data = await api("/assignments/" + saved);
        setForm(data);
        setDirty(false);
        setConsultation(null);
        setNotice("Saved assignment restored.");
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    if (!connected) return;
    const id = setInterval(() => {
      refresh().catch((e) => setError(e.message));
    }, 2000);
    return () => clearInterval(id);
  }, [connected, token]);
  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    setNotice("");
    const body = new FormData();
    body.append("file", file);
    body.append(
      "metadata",
      JSON.stringify({
        department_id: form.department_id,
        title: file.name,
        source_uri: "local-upload://" + encodeURIComponent(file.name),
        access_status: "public",
      }),
    );
    try {
      await api("/documents", { method: "POST", body });
      await refresh();
      setNotice("Upload received. Wait for ready status before selecting it.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    const { assignment_id, ...body } = form;
    // Only contract input fields are sent, never server-generated fields.
    const input = {
      problem: body.problem,
      department_id: body.department_id,
      intended_result: body.intended_result,
      audience: body.audience,
      constraints: body.constraints.map((constraint) => constraint.trim()).filter(Boolean),
      required_sections: body.required_sections.map((section) => section.trim()).filter(Boolean),
      request_type: body.request_type,
      selected_document_version_ids: body.selected_document_version_ids,
    };
    try {
      const saved = await api("/assignments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      localStorage.setItem("assignmentId", saved.assignment_id);
      setForm(saved);
      setDirty(false);
      setConsultation(null);
      setNotice("Assignment saved. Refresh and reconnect to restore it.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function consult() {
    if (!form.assignment_id || dirty) return;
    setBusy(true);
    setError("");
    setConsultation(null);
    try {
      setConsultation(await api(`/assignments/${form.assignment_id}/consult`, { method: "POST" }));
    } catch (e) {
      setError((e as Error).message);
    } finally { setBusy(false); }
  }
  async function find(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = await api("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          selected_document_version_ids: form.selected_document_version_ids
            .length
            ? form.selected_document_version_ids
            : null,
          for_external_model: true,
        }),
      });
      setChunks(result.chunks);
      setSearched(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main>
      <header>
        <p className="eyebrow">AI CORPS / WEEK 2</p>
        <h1>Evidence workspace</h1>
        <p>
          Save a consulting assignment and connect it to readable, traceable
          sources.
        </p>
        <small>
          Local fictional-data demonstration. External model calls are disabled.
        </small>
      </header>
      <section className="connection">
        <label>
          Local demo token
          <input
            type="password"
            disabled={busy || uploading}
            value={token}
            onChange={(e) => {
              setToken(e.target.value);
              setConnected(false);
              setConsultation(null);
              setForm(initial);
              setDocs([]);
              setJobs([]);
              setChunks([]);
              setSearched(false);
              setDirty(false);
            }}
            autoComplete="off"
          />
        </label>
        <button disabled={busy || uploading} onClick={connect}>Connect</button>
        <span>
          {connected
            ? "Connected"
            : "Enter the token from your launch terminal"}
        </span>
      </section>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {connected && (
        <div className="layout">
          <section>
            <h2>1. Assignment</h2>
            <AssignmentForm form={form} docs={docs} busy={busy} onSubmit={save}
              onChange={(value) => { setForm(value); setDirty(true); setConsultation(null); }} />
            <button type="button" disabled={busy || dirty || !form.assignment_id} onClick={consult}>
              Preview mock report
            </button>
            <p className="muted">Save your changes before previewing a report. Reports are temporary previews.</p>
          </section>
          <aside>
            <h2>2. Document input</h2>
            <form onSubmit={upload}>
              <label>
                PDF file
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>
              {file && (
                <p>
                  {file.name} · {Math.ceil(file.size / 1024)} KB
                </p>
              )}
              <p className="muted">
                Default limit: 10 MB. Every page needs readable text.
              </p>
              <button disabled={!file || uploading}>
                {uploading ? "Uploading…" : "Upload PDF"}
              </button>
            </form>
            <h3>Processing status</h3>
            {jobs.length === 0 ? (
              <p>No uploads yet.</p>
            ) : (
              <ul className="jobs">
                {jobs.map((j) => (
                  <li key={j.job_id}>
                    <strong>{j.title}</strong>
                    <span className="state">{j.status}</span>
                    <small>{Math.ceil(j.size_bytes / 1024)} KB</small>
                    {j.error_code && (
                      <p>
                        {guidance[j.error_code] ||
                          j.error_code.replaceAll("_", " ")}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <h2>3. Find evidence</h2>
            <form onSubmit={find}>
              <label>
                Search query
                <input
                  required
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </label>
              <button disabled={busy}>Search evidence</button>
            </form>
            <p className="muted">
              Search selected versions, or all eligible sources if none are
              selected.
            </p>
            {searched && chunks.length === 0 && (
              <p role="status">
                No eligible evidence found. Add an approved source or change the
                query.
              </p>
            )}
            {chunks.map((c) => (
              <article key={c.chunk_id}>
                <h3>
                  {c.title} · {c.locator}
                </h3>
                <p>{c.text}</p>
              </article>
            ))}
          </aside>
        </div>
      )}
      {connected && consultation?.result_type === "report" && (
        <ReportView key={consultation.report.report_id} report={consultation.report} evidence={consultation.evidence} />
      )}
      {connected && consultation?.result_type === "needs_input" && <p role="status">{consultation.questions.join(" ")}</p>}
      {connected && consultation?.result_type === "evidence_gap" && <p role="status">{consultation.message}</p>}
      {connected && consultation?.result_type === "error" && <p role="alert">{consultation.message}</p>}
    </main>
  );
}
