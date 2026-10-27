"""Simple: This file starts the screenshot-friendly Week 5 accomplishment testbench with one command."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.week5_testbench import main

if __name__ == "__main__":
    raise SystemExit(main())

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This is a presentation-friendly entry point. It guarantees imports resolve from
# the repository root, then delegates all validation logic to week5_testbench.
# Keeping this wrapper small prevents demo-only printing from being mixed into the
# scoring, budget, comparison, and regression logic used by automated tests.
