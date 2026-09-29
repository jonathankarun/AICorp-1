from .models import Assignment, ScopeCheckResult


def check_scope(assignment: Assignment) -> ScopeCheckResult:
    missing: list[str] = []
    questions: list[str] = []

    # Week 1 minimum: problem + intended result + enough constraints to begin.
    if not assignment.problem.strip():
        missing.append("problem")
        questions.append("What problem should the City address?")

    if not assignment.intended_result or not assignment.intended_result.strip():
        missing.append("intended_result")
        questions.append("What result or decision should this work product help achieve?")

    if not assignment.department_id:
        missing.append("department_id")
        questions.append("Which department owns or sponsors this request?")

    # An RFQ that only asks for qualifications is not enough to generate a consulting solution.
    if assignment.request_type == "RFQ" and not assignment.constraints:
        missing.append("constraints")
        questions.append(
            "What project scope, constraints, timeline, or deliverables should the qualifications support?"
        )

    if missing:
        return ScopeCheckResult(status="needs_input", questions=questions, missing_fields=missing)
    return ScopeCheckResult(status="ready")
