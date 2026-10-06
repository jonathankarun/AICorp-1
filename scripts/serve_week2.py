"""Start the local fixture demo. Prints a new short-lived local access token."""

import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.data.db import connect, migrate
from backend.data.seed import seed

if __name__ == "__main__":
    if not (ROOT / "apps/web/dist/index.html").exists():
        raise SystemExit(
            "Build the frontend first: npm ci --prefix apps/web && npm run build --prefix apps/web"
        )
    with connect() as conn:
        migrate(conn)
        seed(conn)
    os.environ["AICORP_LOCAL_DEMO"] = "1"
    os.environ.setdefault("AICORP_DEMO_TOKEN", secrets.token_urlsafe(24))
    print("Local fixture demo: http://127.0.0.1:8000", flush=True)
    print("Demo token (local only): " + os.environ["AICORP_DEMO_TOKEN"], flush=True)
    import uvicorn

    uvicorn.run("backend.api.app:app", host="127.0.0.1", port=8000)
