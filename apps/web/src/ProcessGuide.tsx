type Props = { ready: number; selected: number; saved: boolean; results: number; searched: boolean };

export function ProcessGuide({ ready, selected, saved, results, searched }: Props) {
  return <section className="process-guide" aria-labelledby="process-heading">
    <p className="eyebrow">JONATHAN’S CAPSTONE / PROCESS WALKTHROUGH</p>
    <h2 id="process-heading">From source documents to traceable evidence</h2>
    <p>My subsystem turns PDFs and payment records into stored, searchable evidence for the consulting engine. Follow the PDF path below, then demonstrate the spending and review path.</p>
    <ol className="process-steps">
      <li><a href="#document-input">1. Ingest a source</a><p>Upload a readable PDF. The backend validates it, preserves the original file, extracts text by page, and splits it into searchable chunks.</p><strong>{ready} ready source versions</strong></li>
      <li><a href="#assignment">2. Store the assignment</a><p>Select a ready source and save the problem and intended result. PostgreSQL stores the assignment and its exact source versions.</p><strong>{selected} selected · {saved ? 'Assignment saved' : 'Save an assignment to continue'}</strong></li>
      <li><a href="#evidence">3. Retrieve evidence</a><p>Search “timeline” in the bundled example. Keyword retrieval checks source access and returns passages with their page references.</p><strong>{searched ? `${results} passages from the last search` : 'Run a search to see evidence'}</strong></li>
      <li><a href="#evidence">4. Verify the source</a><p>Open the original PDF beside a result and check page 1 for “six weeks”. The passage and source version provide a traceable handoff to the engine.</p><strong>Human verification: compare passage with PDF</strong></li>
    </ol>
    <details><summary>Presenter notes: a three-minute demonstration</summary>
      <p>Upload <code>tests/fixtures/week2/engagement.pdf</code>, wait for ready, select it, and save an assignment such as “Improve permit intake”. Search “timeline” and open the original PDF. Reload and reconnect to show that the saved assignment and selected source persist.</p>
      <p>Then load spending: the imported October CSV starts at $280 consulting, $500 operational, and $50 unresolved. Correct the $50 with a reason to show $330 consulting and an audit record. A previous correction persists, so a repeated demo may already show $330. Search past work for “process” to see evidence-backed facts and explicitly unknown outcomes.</p>
      <p><strong>Subsystem boundary:</strong> this demo performs real local storage, ingestion, retrieval, calculations, and audited corrections. Report storage and reviews are covered by the API and acceptance checks. Live AI generation, production login, and the complete team application are outside this demo.</p>
    </details>
  </section>;
}
