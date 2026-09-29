from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import Assignment, EvidenceChunk, UsageRecord


class ModelAdapter(Protocol):
    call_count: int

    def generate(self, assignment: Assignment, evidence: list[EvidenceChunk]) -> tuple[dict, UsageRecord]:
        ...


class MockModelAdapter:
    """Deterministic Week 1 adapter. No API key or network call is required."""

    def __init__(self, response_path: str | Path):
        self.response_path = Path(response_path)
        self.call_count = 0

    def generate(self, assignment: Assignment, evidence: list[EvidenceChunk]) -> tuple[dict, UsageRecord]:
        self.call_count += 1
        payload = json.loads(self.response_path.read_text())
        payload["assignment_id"] = assignment.assignment_id

        usage = UsageRecord(
            provider="mock",
            model="saved-response-v1",
            prompt_version="v1",
            input_units=len(assignment.problem.split()) + sum(len(e.text.split()) for e in evidence),
            output_units=len(json.dumps(payload).split()),
            mock=True,
        )
        return payload, usage
