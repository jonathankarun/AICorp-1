"""Simple: This script prints a screenshot-friendly demo of the automatic outdated-model replacement system."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.model_lifecycle_testbench import main


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This script adds the repository root to Python's import path so it can find
# the evaluation package when the script is run directly from the command line.
# It then launches the reusable model-lifecycle testbench, which tests outdated
# model detection, replacement selection, benchmark gating, registry updates,
# and rollback history.