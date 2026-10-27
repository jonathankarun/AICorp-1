let manifest = [];
let activeIndex = 0;
const results = new Map();

const el = (id) => document.getElementById(id);
const pretty = (value) => JSON.stringify(value, null, 2);
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {"Content-Type": "application/json", ...(options.headers || {})}
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

function reviewerScores() {
  return {
    accuracy: Number(el("score-accuracy").value),
    completeness: Number(el("score-completeness").value),
    usefulness: Number(el("score-usefulness").value),
    feasibility: Number(el("score-feasibility").value)
  };
}

function renderNav() {
  const list = el("step-list");
  list.innerHTML = "";
  manifest.forEach((item, index) => {
    const b = document.createElement("button");
    b.className = "step" + (index === activeIndex ? " active" : "") + (results.has(item.case_id) ? " done" : "");
    const check = results.has(item.case_id) ? `<span class="checkmark">${results.get(item.case_id).passed ? "✓" : "!"}</span>` : "";
    b.innerHTML = `${check}<strong>${escapeHtml(item.case_id)}</strong> · ${escapeHtml(item.title)}<small>${escapeHtml(item.execution_phase)}</small>`;
    b.onclick = () => selectStep(index);
    list.appendChild(b);
  });
  el("progress-label").textContent = `${results.size} / ${manifest.length}`;
  el("progress-bar").style.width = `${(results.size / manifest.length) * 100}%`;
}

function selectStep(index) {
  activeIndex = index;
  const item = manifest[index];
  renderNav();
  el("case-id").textContent = item.case_id;
  el("case-title").textContent = item.title;
  el("phase-short").textContent = item.execution_phase.replace("Status Update ", "SU ");
  el("owner").textContent = item.plan_owner;
  el("success").textContent = item.success_criteria;
  el("methodology").textContent = item.methodology;
  el("explanation").textContent = item.explanation;
  el("technical").textContent = item.technical_explanation;
  el("run-step").disabled = false;
  el("next-step").disabled = false;
  el("reviewer-panel").classList.toggle("hidden", !item.interactive_reviewer);

  const prior = results.get(item.case_id);
  if (prior) showResult(prior);
  else {
    el("live-status").textContent = "NOT RUN";
    el("live-status").className = "";
    el("headline").textContent = "Run the checkpoint to see evidence.";
    el("input-json").textContent = "Run a checkpoint to populate this panel.";
    el("output-json").textContent = "The engine result will appear here.";
    el("metrics").className = "metrics-empty";
    el("metrics").textContent = "No metrics yet.";
  }
}

function renderMetrics(metrics) {
  const box = el("metrics");
  const entries = Object.entries(metrics || {});
  if (!entries.length) {
    box.className = "metrics-empty";
    box.textContent = "No metrics returned.";
    return;
  }
  box.className = "metrics";
  box.innerHTML = entries.map(([key, value]) =>
    `<div class="metric"><span>${escapeHtml(key.replaceAll("_", " "))}</span><strong>${escapeHtml(value)}</strong></div>`
  ).join("");
}

function showResult(result) {
  el("live-status").textContent = result.passed ? "PASS" : "FAIL";
  el("live-status").className = result.passed ? "pass" : "fail";
  el("headline").textContent = result.headline;
  el("input-json").textContent = pretty(result.input);
  el("output-json").textContent = pretty(result.output);
  renderMetrics(result.metrics);
}

async function runActive() {
  const item = manifest[activeIndex];
  el("run-step").disabled = true;
  el("live-status").textContent = "RUNNING…";
  try {
    const body = item.interactive_reviewer ? {reviewer_scores: reviewerScores()} : {};
    const result = await api(`/api/demo/run/${encodeURIComponent(item.case_id)}`, {
      method: "POST", body: JSON.stringify(body)
    });
    results.set(item.case_id, result);
    showResult(result);
    renderNav();
  } catch (error) {
    el("live-status").textContent = "ERROR";
    el("live-status").className = "fail";
    el("headline").textContent = error.message;
  } finally {
    el("run-step").disabled = false;
  }
}

async function runAll() {
  el("run-all").disabled = true;
  el("run-all").textContent = "Running…";
  try {
    const result = await api("/api/demo/run-all", {
      method: "POST", body: JSON.stringify({reviewer_scores: reviewerScores()})
    });
    result.results.forEach(r => results.set(r.case_id, r));
    selectStep(activeIndex);
    renderNav();
  } finally {
    el("run-all").disabled = false;
    el("run-all").textContent = "Run all checks";
  }
}

function listHtml(items) {
  return (items || []).length
    ? items.map(item => `<li>${escapeHtml(item)}</li>`).join("")
    : "<li>None recorded.</li>";
}

function renderFinalHandoff(payload) {
  const display = payload.application_display;
  el("final-empty").classList.add("hidden");
  el("final-output").classList.remove("hidden");
  el("final-status").textContent = payload.status === "succeeded" ? "Ready for application display" : "Run failed";
  el("final-status").className = `final-status ${payload.status === "succeeded" ? "success" : "failure"}`;
  if (!display) return;

  el("handoff-meta").innerHTML = [
    ["Run ID", payload.run.run_id],
    ["Run status", payload.run.status],
    ["Report ID", payload.report_contract.report_id],
    ["Report version", payload.report_contract.version],
  ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");

  el("report-status").textContent = display.status_label;
  el("report-title").textContent = display.title;
  el("report-problem").textContent = display.problem;

  el("report-sections").innerHTML = display.sections.map(section => {
    const sources = section.sources.map(source =>
      `<span class="source-chip">${escapeHtml(source.citation_id)} · ${escapeHtml(source.title)} · ${escapeHtml(source.locator)}</span>`
    ).join("");
    return `<section class="report-section"><h3>${escapeHtml(section.label)}</h3><p>${escapeHtml(section.content)}</p><div class="source-inline">${sources}</div></section>`;
  }).join("");

  el("report-assumptions").innerHTML = listHtml(display.assumptions);
  el("report-missing").innerHTML = listHtml(display.missing_information);
  el("report-review").innerHTML = listHtml(display.expert_review_needed);

  el("quality-summary").innerHTML = Object.entries(display.quality_summary).map(([key, value]) =>
    `<div class="quality-item"><span>${escapeHtml(key.replaceAll("_", " "))}</span><strong>${escapeHtml(value)}</strong></div>`
  ).join("");

  el("source-cards").innerHTML = display.sources.map(source =>
    `<article class="source-card"><strong>${escapeHtml(source.title)}</strong><span>${escapeHtml(source.citation_id)} · ${escapeHtml(source.locator)}</span><p>${escapeHtml(source.text)}</p></article>`
  ).join("");

  el("handoff-json").textContent = pretty(payload);
  el("final-section").scrollIntoView({behavior: "smooth", block: "start"});
}

async function runFinal() {
  el("run-final").disabled = true;
  el("run-final").textContent = "Running final assignment…";
  el("final-status").textContent = "Running";
  try {
    const payload = await api("/api/demo/final-handoff", {method: "POST", body: "{}"});
    renderFinalHandoff(payload);
  } catch (error) {
    el("final-status").textContent = "Error";
    el("final-status").className = "final-status failure";
    el("final-empty").textContent = error.message;
  } finally {
    el("run-final").disabled = false;
    el("run-final").textContent = "Run final fake assignment";
  }
}

function reset() {
  results.clear();
  activeIndex = 0;
  renderNav();
  selectStep(0);
}

el("run-step").onclick = runActive;
el("run-all").onclick = runAll;
el("run-final").onclick = runFinal;
el("reset").onclick = reset;
el("next-step").onclick = () => selectStep((activeIndex + 1) % manifest.length);

api("/api/demo/manifest").then(data => {
  manifest = data.cases;
  el("subtitle").textContent = data.subtitle;
  renderNav();
  selectStep(0);
}).catch(err => {
  el("headline").textContent = "Could not load demo manifest: " + err.message;
});
