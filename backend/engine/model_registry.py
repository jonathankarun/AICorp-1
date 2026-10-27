"""Simple: This file detects outdated AI models, finds approved replacements, and safely updates the model registry."""

from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import httpx

@dataclass(frozen=True)
class ModelRecord:
    provider: str
    model_id: str
    lifecycle: str = "active"
    created_at: str | None = None
    shutdown_date: str | None = None

def load_registry(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())

def save_registry(path: str | Path, registry: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(registry, indent=2) + "\n")

def load_fixture_catalog(path: str | Path) -> dict[str, list[ModelRecord]]:
    payload = json.loads(Path(path).read_text())
    return {
        provider: [
            ModelRecord(
                provider=provider,
                model_id=item["model_id"],
                lifecycle=item.get("lifecycle", "active"),
                created_at=item.get("created_at"),
                shutdown_date=item.get("shutdown_date"),
            )
            for item in items
        ]
        for provider, items in payload["providers"].items()
    }

def fetch_openai_models(api_key: str) -> list[ModelRecord]:
    r = httpx.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15.0,
    )
    r.raise_for_status()
    records = []
    for item in r.json().get("data", []):
        created = item.get("created")
        created_at = (
            datetime.utcfromtimestamp(created).date().isoformat()
            if isinstance(created, (int, float))
            else None
        )
        shutdown = item.get("shutdown_date")
        records.append(ModelRecord(
            provider="openai",
            model_id=item["id"],
            lifecycle="deprecated" if shutdown else "active",
            created_at=created_at,
            shutdown_date=shutdown,
        ))
    return records

def fetch_anthropic_models(api_key: str) -> list[ModelRecord]:
    r = httpx.get(
        "https://api.anthropic.com/v1/models?limit=1000",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout=15.0,
    )
    r.raise_for_status()
    return [
        ModelRecord(
            provider="anthropic",
            model_id=item["id"],
            lifecycle=item.get("lifecycle", "active"),
            created_at=item.get("created_at"),
        )
        for item in r.json().get("data", [])
    ]

def needs_refresh(entry, catalog, *, today: date, warning_days: int):
    current = next((m for m in catalog if m.model_id == entry["active_model_id"]), None)
    if current is None:
        return True, "configured model is missing from provider catalog"
    if current.lifecycle in {"deprecated", "retired"}:
        return True, f"configured model lifecycle is {current.lifecycle}"
    if current.shutdown_date:
        shutdown = date.fromisoformat(current.shutdown_date[:10])
        if shutdown <= today + timedelta(days=warning_days):
            return True, f"configured model shuts down in {(shutdown - today).days} day(s)"
    return False, "configured model is active"

def choose_replacement(entry, catalog):
    prefixes = tuple(entry.get("allowed_model_prefixes", []))
    candidates = [
        m for m in catalog
        if m.model_id != entry["active_model_id"]
        and m.lifecycle == "active"
        and (not prefixes or any(m.model_id.startswith(p) for p in prefixes))
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda m: (m.created_at or "0000-00-00", m.model_id), reverse=True)
    return candidates[0]

def plan_refreshes(registry, catalogs, *, today: date):
    warning_days = int(registry.get("refresh_warning_days", 60))
    proposals = []
    for entry in registry["models"]:
        catalog = catalogs.get(entry["provider"], [])
        refresh, reason = needs_refresh(entry, catalog, today=today, warning_days=warning_days)
        replacement = choose_replacement(entry, catalog) if refresh else None
        proposals.append({
            "name": entry["name"],
            "provider": entry["provider"],
            "current_model_id": entry["active_model_id"],
            "needs_refresh": refresh,
            "reason": reason,
            "replacement_model_id": replacement.model_id if replacement else None,
        })
    return proposals

def apply_approved_refreshes(registry, proposals, benchmark_results, *, today: date):
    updated = json.loads(json.dumps(registry))
    benchmarks = {x["name"]: x for x in benchmark_results.get("candidates", [])}
    changes = []
    for proposal in proposals:
        replacement = proposal.get("replacement_model_id")
        benchmark = benchmarks.get(proposal["name"])
        if not proposal["needs_refresh"] or not replacement or not benchmark:
            continue
        if benchmark.get("model_id") != replacement or benchmark.get("passed") is not True:
            continue
        entry = next(x for x in updated["models"] if x["name"] == proposal["name"])
        old = entry["active_model_id"]
        entry.setdefault("history", []).append({
            "model_id": old,
            "replaced_on": today.isoformat(),
            "reason": proposal["reason"],
        })
        entry["active_model_id"] = replacement
        entry["last_refreshed_on"] = today.isoformat()
        changes.append({
            "name": proposal["name"],
            "old_model_id": old,
            "new_model_id": replacement,
            "benchmark_passed": True,
        })
    return updated, changes

# TECHNICAL EXPLANATION:
# Provider-specific model catalogs are normalized into ModelRecord objects.
# The planner flags missing/deprecated/retired/soon-to-shutdown models, limits
# replacements to approved model-family prefixes, and selects the newest active
# candidate. The active registry changes only when a matching benchmark result
# has passed, and the previous model is retained in history for audit/rollback.
