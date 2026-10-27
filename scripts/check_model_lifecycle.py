"""Simple: This script checks whether configured AI models are outdated and creates a replacement proposal."""

from __future__ import annotations
import argparse, json, os
from datetime import date
from pathlib import Path
from backend.engine.model_registry import (
    apply_approved_refreshes, fetch_anthropic_models, fetch_openai_models,
    load_fixture_catalog, load_registry, plan_refreshes, save_registry,
)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--live", action="store_true")
    p.add_argument("--apply-approved", action="store_true")
    p.add_argument("--registry", default="config/model_registry.json")
    p.add_argument("--benchmark-results", default="evaluation/model_refresh_benchmark_fixture.json")
    p.add_argument("--proposal-output", default="evidence/model-lifecycle/proposed_model_registry.json")
    args = p.parse_args()
    if args.fixture == args.live:
        p.error("Choose exactly one of --fixture or --live")

    registry = load_registry(args.registry)
    if args.fixture:
        catalogs = load_fixture_catalog("evaluation/model_lifecycle_fixture.json")
    else:
        catalogs = {}
        if os.getenv("OPENAI_API_KEY"):
            catalogs["openai"] = fetch_openai_models(os.environ["OPENAI_API_KEY"])
        if os.getenv("ANTHROPIC_API_KEY"):
            catalogs["anthropic"] = fetch_anthropic_models(os.environ["ANTHROPIC_API_KEY"])

    proposals = plan_refreshes(registry, catalogs, today=date.today())
    output = {"checked_on": date.today().isoformat(), "proposals": proposals}

    if args.apply_approved:
        benchmark = json.loads(Path(args.benchmark_results).read_text())
        updated, changes = apply_approved_refreshes(
            registry, proposals, benchmark, today=date.today()
        )
        save_registry(args.proposal_output, updated)
        output["changes"] = changes
        output["proposal_output"] = args.proposal_output

    print(json.dumps(output, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# TECHNICAL EXPLANATION:
# Fixture mode supports repeatable demos. Live mode reads provider catalogs using
# API keys from environment variables. Even with --apply-approved, the script
# writes a proposed registry rather than silently overwriting the active one.
