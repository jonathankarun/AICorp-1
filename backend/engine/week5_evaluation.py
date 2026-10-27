"""Simple: This file scores report quality, calculates cost, blocks overspending, and freezes the Week 5 configuration."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from uuid import uuid4


MONEY = Decimal("0.000001")


@dataclass(frozen=True)
class ProviderRate:
    model_id: str
    rate_date: str
    rate_unit_tokens: int
    input_rate_usd: Decimal
    output_rate_usd: Decimal

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderRate":
        return cls(
            model_id=data["model_id"],
            rate_date=data["rate_date"],
            rate_unit_tokens=int(data.get("rate_unit_tokens", 1000)),
            input_rate_usd=Decimal(str(data["input_rate_usd"])),
            output_rate_usd=Decimal(str(data["output_rate_usd"])),
        )


@dataclass(frozen=True)
class UsageRecord:
    model_id: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int
    retries: int = 0
    revisions: int = 0
    embedding_cost_usd: Decimal = Decimal("0")
    usage_source: str = "fixture_estimate"
    billing_uncertain: bool = False


class BudgetExceeded(RuntimeError):
    pass


class BudgetLedger:
    """Small atomic reservation ledger used before any paid/provider call.

    The lock matters because two simultaneous requests must not reserve the same
    remaining balance. The fixture runner is single-process, but the behavior is
    directly testable here before a persistent implementation is adopted.
    """

    def __init__(self, allowance_usd: Decimal | str):
        self.allowance_usd = Decimal(str(allowance_usd))
        self._spent = Decimal("0")
        self._reservations: dict[str, Decimal] = {}
        self._lock = threading.Lock()

    @property
    def spent_usd(self) -> Decimal:
        with self._lock:
            return self._spent

    @property
    def reserved_usd(self) -> Decimal:
        with self._lock:
            return sum(self._reservations.values(), Decimal("0"))

    @property
    def remaining_usd(self) -> Decimal:
        with self._lock:
            return self.allowance_usd - self._spent - sum(
                self._reservations.values(), Decimal("0")
            )

    def reserve(self, maximum_cost_usd: Decimal) -> str:
        maximum_cost_usd = Decimal(maximum_cost_usd)
        if maximum_cost_usd < 0:
            raise ValueError("maximum_cost_usd cannot be negative")
        with self._lock:
            already_reserved = sum(self._reservations.values(), Decimal("0"))
            remaining = self.allowance_usd - self._spent - already_reserved
            if maximum_cost_usd > remaining:
                raise BudgetExceeded(
                    f"reserved maximum ${maximum_cost_usd:.6f} exceeds remaining "
                    f"allowance ${remaining:.6f}"
                )
            reservation_id = str(uuid4())
            self._reservations[reservation_id] = maximum_cost_usd
            return reservation_id

    def reconcile(self, reservation_id: str, actual_cost_usd: Decimal) -> None:
        actual_cost_usd = Decimal(actual_cost_usd)
        with self._lock:
            if reservation_id not in self._reservations:
                raise KeyError(f"unknown reservation: {reservation_id}")
            reserved = self._reservations.pop(reservation_id)
            # A correct caller should reserve conservatively. If actual exceeds
            # reserved, keep the real spend and expose the error to the caller.
            self._spent += actual_cost_usd
            if actual_cost_usd > reserved:
                raise RuntimeError(
                    f"actual cost ${actual_cost_usd:.6f} exceeded reservation "
                    f"${reserved:.6f}"
                )

    def cancel(self, reservation_id: str) -> None:
        with self._lock:
            self._reservations.pop(reservation_id, None)


def compute_cost(usage: UsageRecord, rate: ProviderRate) -> Decimal:
    input_cost = (
        Decimal(usage.input_tokens)
        / Decimal(rate.rate_unit_tokens)
        * rate.input_rate_usd
    )
    output_cost = (
        Decimal(usage.output_tokens)
        / Decimal(rate.rate_unit_tokens)
        * rate.output_rate_usd
    )
    total = input_cost + output_cost + usage.embedding_cost_usd
    return total.quantize(MONEY, rounding=ROUND_HALF_UP)


def reserve_maximum_cost(
    *,
    input_token_estimate: int,
    output_token_cap: int,
    rate: ProviderRate,
    embedding_allowance_usd: Decimal | str = Decimal("0"),
) -> Decimal:
    if input_token_estimate < 0 or output_token_cap < 0:
        raise ValueError("token estimates cannot be negative")
    projected = compute_cost(
        UsageRecord(
            model_id=rate.model_id,
            input_tokens=input_token_estimate,
            output_tokens=output_token_cap,
            elapsed_ms=0,
            embedding_cost_usd=Decimal(str(embedding_allowance_usd)),
        ),
        rate,
    )
    return projected


def canonical_fingerprint(assignment: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {"assignment": assignment, "evidence": evidence},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def estimate_input_tokens(
    assignment: dict[str, Any],
    evidence: list[dict[str, Any]],
    *,
    prompt_overhead_tokens: int = 180,
) -> int:
    """Conservative local estimate for budget reservation.

    This is intentionally not presented as provider-reported token usage.
    """
    text = json.dumps(
        {"assignment": assignment, "evidence": evidence},
        sort_keys=True,
    )
    # Rough four-characters-per-token estimate, rounded up, plus prompt overhead.
    return max(1, (len(text) + 3) // 4) + int(prompt_overhead_tokens)


def deduplicate_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    removed: list[str] = []
    for item in evidence:
        normalized = " ".join(str(item.get("text", "")).lower().split())
        key = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if key in seen:
            removed.append(str(item.get("chunk_id", "")))
            continue
        seen.add(key)
        kept.append(item)
    return kept, removed


def score_result(
    result: dict[str, Any],
    *,
    required_sections: list[str],
    reviewer: dict[str, Any],
) -> dict[str, Any]:
    """Score the exact dimensions named in the Week 5 guide.

    Automated checks cover structure/citations/support. Usefulness and feasibility
    are explicitly reviewer scores and remain labeled peer/City review.
    """
    reviewer_type = reviewer.get("reviewer_type", "peer")
    usefulness = float(reviewer.get("usefulness", 0))
    feasibility = float(reviewer.get("feasibility", 0))
    if not 0 <= usefulness <= 5 or not 0 <= feasibility <= 5:
        raise ValueError("reviewer usefulness/feasibility must be between 0 and 5")

    if result.get("result_type") != "report":
        critical = 1 if result.get("code") in {
            "invalid_citation",
            "unsupported_numeric_claim",
            "missing_required_sections",
        } else 0
        return {
            "result_type": result.get("result_type", "error"),
            "total_score": 0.0,
            "required_section_coverage_pct": 0.0,
            "factual_support_pct": 0.0,
            "citation_quality_pct": 0.0,
            "completeness_pct": 0.0,
            "usefulness_score_1_to_5": usefulness,
            "feasibility_score_1_to_5": feasibility,
            "reviewer_type": reviewer_type,
            "critical_unsupported_claims": critical,
            "failure_code": result.get("code"),
        }

    report = result["report"]
    sections = report.get("sections", [])
    returned_names = {section.get("name") for section in sections}
    required = set(required_sections)
    coverage = (len(required & returned_names) / len(required)) if required else 1.0

    support_checks = result.get("support_checks", [])
    if support_checks:
        support_values = []
        for check in support_checks:
            status = check.get("status")
            if status == "supported":
                support_values.append(1.0)
            elif status == "human_review_required":
                support_values.append(0.5)
            else:
                support_values.append(0.0)
        support = sum(support_values) / len(support_values)
    else:
        support = 0.0

    if sections:
        cited_sections = sum(bool(section.get("citation_ids")) for section in sections)
        citation_quality = cited_sections / len(sections)
        nonblank = sum(bool(str(section.get("content", "")).strip()) for section in sections)
        completeness = nonblank / len(sections)
    else:
        citation_quality = 0.0
        completeness = 0.0

    critical = sum(
        1
        for check in support_checks
        if check.get("status") == "unsupported_numeric_claim"
    )

    # 100-point sheet:
    # required sections 20, factual support 25, citation quality 20,
    # completeness 15, usefulness 10, feasibility 10.
    total = (
        coverage * 20
        + support * 25
        + citation_quality * 20
        + completeness * 15
        + (usefulness / 5.0) * 10
        + (feasibility / 5.0) * 10
    )

    return {
        "result_type": "report",
        "total_score": round(total, 2),
        "required_section_coverage_pct": round(coverage * 100, 1),
        "factual_support_pct": round(support * 100, 1),
        "citation_quality_pct": round(citation_quality * 100, 1),
        "completeness_pct": round(completeness * 100, 1),
        "usefulness_score_1_to_5": usefulness,
        "feasibility_score_1_to_5": feasibility,
        "reviewer_type": reviewer_type,
        "critical_unsupported_claims": critical,
        "failure_code": None,
    }


def meets_quality_gate(candidate_summary: dict[str, Any], gate: dict[str, Any]) -> bool:
    if gate.get("require_all_runs_success", True) and candidate_summary["failures"] != 0:
        return False
    if candidate_summary["average_score"] < float(gate["minimum_average_score"]):
        return False
    if candidate_summary["critical_unsupported_claims"] > int(
        gate.get("max_critical_unsupported_claims", 0)
    ):
        return False
    if candidate_summary["minimum_required_section_coverage_pct"] < float(
        gate.get("minimum_required_section_coverage_pct", 100)
    ):
        return False
    return True


def choose_lowest_cost_passing(
    summaries: list[dict[str, Any]],
    gate: dict[str, Any],
) -> dict[str, Any] | None:
    passing = [item for item in summaries if meets_quality_gate(item, gate)]
    if not passing:
        return None
    return min(
        passing,
        key=lambda item: (
            Decimal(str(item["average_cost_usd"])),
            -float(item["average_score"]),
            item["candidate_id"],
        ),
    )


def freeze_configuration(
    path: str | Path,
    *,
    selected: dict[str, Any] | None,
    manifest: dict[str, Any],
    tuning: dict[str, Any],
) -> dict[str, Any]:
    frozen = {
        "status": "frozen" if selected else "no_candidate_met_quality_gate",
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "model_id": selected["model_id"] if selected else None,
        "prompt_version": manifest["prompt_version"],
        "retrieval_version": manifest["retrieval_version"],
        "corpus_version": manifest["corpus_version"],
        "deduplicate_context": tuning["deduplicate_context"],
        "quality_gate": manifest["quality_gate"],
        "rate_schedule_label": manifest["rate_schedule_label"],
        "note": (
            "Fixture comparison only; replace fixture usage/rates with authorized "
            "provider-reported values before making a live-provider claim."
        ),
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frozen, indent=2))
    return frozen

# ---------------------------------------------------------------------------
# TECHNICAL EXPLANATION
# This module owns the deterministic Week 5 evaluation logic. ProviderRate and
# UsageRecord normalize usage/cost inputs; BudgetLedger performs an atomic
# reservation before any provider call; score_result applies the 100-point
# quality rubric; deduplicate_evidence measures a targeted context improvement;
# choose_lowest_cost_passing enforces the quality gate before cost optimization;
# and freeze_configuration records the selected prompt/retrieval/model settings
# for the Week 6 baseline. No live-provider claim is made by this fixture path.
