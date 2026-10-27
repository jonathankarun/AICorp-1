"""Simple: This script starts Jai's complete subsystem demo and opens the walkthrough in a browser."""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Jai's final LLM engine walkthrough")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("=" * 72)
    print("JAI — LLM CONSULTING ENGINE FINAL DEMO")
    print("=" * 72)
    print(f"Open: {url}")
    print("Mode: deterministic local acceptance fixtures; no API key required.")
    print("Use each checkpoint's Run button, pause to explain, then click Next.")
    print("=" * 72)

    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "backend.engine.final_demo_api:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="warning",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# The launcher inserts the repository root into sys.path, starts the dedicated
# FastAPI demo app with Uvicorn, and opens the local browser. Keeping the final
# demo on port 8010 avoids interfering with the team's existing Week 2 workspace
# on port 8000. The browser can be suppressed with --no-browser for CI or remote
# environments.
