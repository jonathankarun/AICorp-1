import { useEffect, useState } from "react";
import { checkHealth } from "./api";
import { AssignmentForm } from "./components/AssignmentForm";
import { ReportView } from "./components/ReportView";
import { MOCK_EVIDENCE, MOCK_REPORT } from "./mockReport";
import type { AssignmentResponse } from "./types";
import "./styles.css";

export default function App() {
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [created, setCreated] = useState<AssignmentResponse | null>(null);

  useEffect(() => {
    checkHealth().then(setApiHealthy).catch(() => setApiHealthy(false));
  }, []);

  return (
    <main className="page-shell">
      <header>
        <p className="eyebrow">AI Corps · Yasha · Week 1</p>
        <h1>Assignment workflow demo</h1>
        <p>
          Enter a consulting need, send a typed request to FastAPI, then inspect a
          Jai-compatible structured report fixture and its source evidence.
        </p>
        <div className={apiHealthy ? "health ok" : "health bad"}>
          API: {apiHealthy === null ? "checking…" : apiHealthy ? "connected" : "offline"}
        </div>
      </header>

      <AssignmentForm onCreated={setCreated} />

      {created && (
        <section className="success card" aria-label="assignment success">
          <h2>Assignment created</h2>
          <p><strong>ID:</strong> {created.assignment_id}</p>
          <p>Server normalized the payload under schema {created.schema_version}.</p>
        </section>
      )}

      <ReportView report={MOCK_REPORT} evidence={MOCK_EVIDENCE} />
    </main>
  );
}
