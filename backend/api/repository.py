"""Temporary Week 1 in-memory assignment repository.

The weekly guide explicitly allows an in-memory repository for Week 1 as long as its
limitation is documented. Week 2 replaces this adapter with Jonny's persistence layer
without changing the public API contract.
"""

from dataclasses import dataclass, field

from .models import AssignmentResponse


@dataclass
class InMemoryAssignmentRepository:
    """Small fake repository used to make the workflow runnable before the DB is ready."""

    assignments: dict[str, AssignmentResponse] = field(default_factory=dict)

    def create(self, assignment: AssignmentResponse) -> AssignmentResponse:
        self.assignments[assignment.assignment_id] = assignment
        return assignment

    def get(self, assignment_id: str) -> AssignmentResponse | None:
        return self.assignments.get(assignment_id)

    def clear(self) -> None:
        """Test helper so each test begins with a known empty repository."""
        self.assignments.clear()
