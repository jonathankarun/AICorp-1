from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from .demo_models import Assignment, EvidenceChunk, UsageRecord


class ModelAdapter(Protocol):
    call_count: int

    def generate(
        self,
        assignment: Assignment,
        evidence: list[EvidenceChunk],
        generation_context: dict[str, Any] | None = None,
    ) -> tuple[dict, UsageRecord]:
        ...


class MockModelAdapter:
    """Deterministic adapter used for repeatable demos and CI; no API key required."""

    def __init__(self, response_path: str | Path, prompt_version: str = "v1"):
        self.response_path = Path(response_path)
        self.prompt_version = prompt_version
        self.call_count = 0
        self.last_evidence_ids: list[str] = []
        self.last_context: dict[str, Any] = {}

    def generate(
        self,
        assignment: Assignment,
        evidence: list[EvidenceChunk],
        generation_context: dict[str, Any] | None = None,
    ) -> tuple[dict, UsageRecord]:
        self.call_count += 1
        self.last_evidence_ids = [item.chunk_id for item in evidence]
        self.last_context = generation_context or {}

        payload = json.loads(self.response_path.read_text())
        payload["assignment_id"] = assignment.assignment_id

        context_words = len(json.dumps(self.last_context).split())
        usage = UsageRecord(
            provider="mock",
            model="saved-response-v1",
            prompt_version=self.prompt_version,
            input_units=(
                len(assignment.problem.split())
                + sum(len(e.text.split()) for e in evidence)
                + context_words
            ),
            output_units=len(json.dumps(payload).split()),
            elapsed_ms=0,
            mock=True,
        )
        return payload, usage
