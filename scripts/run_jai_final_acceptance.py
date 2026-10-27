"""Simple: This script runs every Jai validation checkpoint at once and saves the final acceptance evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.jai_final_validation import run_all, run_final_application_handoff


def main() -> int:
    result = run_all()
    handoff = run_final_application_handoff()
    out = ROOT / "evidence" / "final" / "jai"
    out.mkdir(parents=True, exist_ok=True)
    (out / "acceptance_results.json").write_text(json.dumps(result, indent=2))
    (out / "yasha_display_payload.json").write_text(json.dumps(handoff, indent=2))

    lines = [
        "JAI — LLM CONSULTING ENGINE FINAL ACCEPTANCE",
        "=" * 86,
        f"Required validation cases: {result['required_validation_passed']}/{result['required_validation_cases']}",
        f"All demo cases (including longevity bonus): {result['passed_cases']}/{result['total_cases']}",
        f"Final application handoff: {handoff['status']}",
        "",
        f"{'ID':<10} {'PASS?':<7} {'CHECK':<46} METRIC",
        "-" * 100,
    ]
    for item in result["results"]:
        metric = ", ".join(f"{k}={v}" for k, v in list(item["metrics"].items())[:2])
        lines.append(
            f"{item['case_id']:<10} "
            f"{('PASS' if item['passed'] else 'FAIL'):<7} "
            f"{item['title']:<46} "
            f"{metric}"
        )
    lines.extend(
        [
            "",
            "FINAL STATUS: " + (
                "JAI ENGINE ACCEPTANCE COMPLETE"
                if result["required_validation_complete"]
                else "VALIDATION ACTION REQUIRED"
            ),
            "",
            "Note: this final acceptance uses controlled synthetic fixtures. Shared",
            "database/browser integration and any live-provider benchmark remain separate",
            "full-team deployment evidence rather than being falsely claimed here.",
        ]
    )
    rendered = "\n".join(lines)
    print(rendered)
    (out / "acceptance_summary.txt").write_text(rendered + "\n")
    return 0 if result["required_validation_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This CLI provides a non-GUI acceptance path for CI and submission evidence.
# It invokes the exact same run_all() function used by the browser demo, saves
# machine-readable JSON and a screenshot-friendly summary, and exits nonzero if
# any required VP-* validation case fails. The EXTRA longevity check is reported
# but does not redefine the course validation plan.
