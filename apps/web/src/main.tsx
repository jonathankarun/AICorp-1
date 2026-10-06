import { useEffect, useState, type FormEvent } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Document = {
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
type Assignment = {
  problem: string;
  department_id: string;
  intended_result: string;
  audience: string;
  constraints: string[];
  required_sections: string[];
  selected_document_version_ids: string[];
  assignment_id?: string;
};
const initial: Assignment = {
  problem: "",
  department_id: "10000000-0000-4000-8000-000000000001",
  intended_result: "",
  audience: "Department leadership",
  constraints: [],
  required_sections: ["findings", "recommendation"],
  selected_document_version_ids: [],
};
const guidance: Record<string, string> = {
  file_too_large: "Reduce the file size and try again.",
  pdf_required: "Choose a PDF file.",
  empty_or_scanned_page: "Choose a PDF with readable text on every page.",
  unreadable_pdf: "Choose a readable, uncorrupted PDF.",
  unauthorized: "Check your local demo token.",
  database_unavailable:
    "Database unavailable. Restore the database connection and retry.",
  source_not_ready_or_not_allowed:
    "Select only ready sources you are allowed to use.",
};
function App() {
  const [token, setToken] = useState(sessionStorage.getItem("demoToken") || "");
  const [connected, setConnected] = useState(false);
  const [form, setForm] = useState<Assignment>(initial);
  const [docs, setDocs] = useState<Document[]>([]),
    [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false),
    [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState(""),
    [chunks, setChunks] = useState<Chunk[]>([]),
    [searched, setSearched] = useState(false);
  async function api(path: string, options: RequestInit = {}) {
    const response = await fetch("/api/v1" + path, {
      ...options,
      headers: { Authorization: "Bearer " + token, ...options.headers },
    });
    const body = await response.json();
    if (!response.ok) {
      const code = body.error?.code || "request_failed";
      throw new Error(guidance[code] || code.replaceAll("_", " "));
    }
    return body;
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
    try {
      await refresh();
      sessionStorage.setItem("demoToken", token);
      setConnected(true);
      const saved = localStorage.getItem("assignmentId");
      if (saved) {
        const data = await api("/assignments/" + saved);
        setForm(data);
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
      constraints: body.constraints,
      required_sections: body.required_sections,
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
      setNotice("Assignment saved. Refresh and reconnect to restore it.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
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
            value={token}
            onChange={(e) => {
              setToken(e.target.value);
              setConnected(false);
            }}
            autoComplete="off"
          />
        </label>
        <button onClick={connect}>Connect</button>
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
            <form onSubmit={save}>
              <label>
                Problem
                <textarea
                  aria-label="Problem"
                  required
                  value={form.problem}
                  onChange={(e) =>
                    setForm({ ...form, problem: e.target.value })
                  }
                />
              </label>
              <label>
                Intended result
                <input
                  required
                  value={form.intended_result}
                  onChange={(e) =>
                    setForm({ ...form, intended_result: e.target.value })
                  }
                />
              </label>
              <label>
                Audience
                <input
                  value={form.audience}
                  onChange={(e) =>
                    setForm({ ...form, audience: e.target.value })
                  }
                />
              </label>
              <label>
                Constraints (one per line)
                <textarea
                  aria-label="Constraints (one per line)"
                  value={form.constraints.join("\n")}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      constraints: e.target.value.split("\n"),
                    })
                  }
                />
              </label>
              <p className="muted">
                Department: Fictional department. Choose ready sources below
                before saving.
              </p>
              <fieldset>
                <legend>Ready sources</legend>
                {docs.length === 0 ? (
                  <p>No ready sources yet.</p>
                ) : (
                  docs.map((d) => (
                    <label className="check" key={d.document_version_id}>
                      <input
                        type="checkbox"
                        checked={form.selected_document_version_ids.includes(
                          d.document_version_id,
                        )}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            selected_document_version_ids: e.target.checked
                              ? [
                                  ...form.selected_document_version_ids,
                                  d.document_version_id,
                                ]
                              : form.selected_document_version_ids.filter(
                                  (id) => id !== d.document_version_id,
                                ),
                          })
                        }
                      />
                      <span>
                        {d.title} · v{d.version}
                        <small>
                          {d.external_model_allowed
                            ? "Eligible for model context"
                            : "Read-only evidence; external model use not approved"}
                        </small>
                      </span>
                    </label>
                  ))
                )}
              </fieldset>
              <button disabled={busy}>
                {busy ? "Working…" : "Save assignment"}
              </button>
              {form.assignment_id && (
                <p className="muted">Saved ID: {form.assignment_id}</p>
              )}
            </form>
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
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
