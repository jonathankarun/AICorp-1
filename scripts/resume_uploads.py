"""After stopping the API, resume durable pending/interrupted PDF jobs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.data.db import connect
from backend.data.ingestion import process_job

with connect() as conn:
    jobs = conn.execute(
        "SELECT job_id FROM ingestion_jobs WHERE status IN ('pending','processing') ORDER BY created_at"
    ).fetchall()
for job in jobs:
    with connect() as conn:
        state = process_job(conn, job["job_id"])
        print(job["job_id"], state)
