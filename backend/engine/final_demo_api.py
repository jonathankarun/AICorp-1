"""Simple: This file exposes Jai's final validation testbench to a local browser GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from evaluation.jai_final_validation import case_manifest, run_all, run_case, run_final_application_handoff

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "demo" / "jai_engine"

app = FastAPI(
    title="Jai LLM Consulting Engine Final Demo",
    description="Local-only validation and walkthrough UI for the AI Corps capstone.",
)

app.mount("/assets", StaticFiles(directory=DEMO_DIR), name="jai-demo-assets")


@app.get("/")
def index():
    return FileResponse(DEMO_DIR / "index.html")


@app.get("/api/demo/manifest")
def manifest():
    return {
        "title": "Jai — LLM Consulting Engine Final Acceptance Demo",
        "subtitle": "Execution plan + validation plan + end-to-end walkthrough",
        "cases": case_manifest(),
    }


@app.post("/api/demo/run/{case_id}")
def execute_case(case_id: str, payload: dict[str, Any] = Body(default={})):
    try:
        reviewer_scores = payload.get("reviewer_scores")
        return run_case(case_id, reviewer_scores)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/demo/run-all")
def execute_all(payload: dict[str, Any] = Body(default={})):
    return run_all(payload.get("reviewer_scores"))


@app.post("/api/demo/final-handoff")
def final_handoff():
    return run_final_application_handoff()


@app.get("/api/demo/health")
def health():
    return {"status": "ok", "mode": "local_fixture_acceptance"}


# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# FastAPI is used only as a local presentation boundary. It does not duplicate
# validation logic: every endpoint delegates to evaluation/jai_final_validation.py.
# StaticFiles serves the self-contained HTML/CSS/JS interface, while the API
# returns structured JSON that the browser can render at each presentation
# explanation. No model API key, database connection, or external network request
# is required for the deterministic acceptance demonstration.
