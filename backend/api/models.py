"""Typed request/response models for Yasha's Week 1 application API.

The fields intentionally mirror Jai's current Week 1 Assignment model where possible,
while the API adds the server-owned ``created_by`` field to the create response.
Jonny's data module currently uses UUID department IDs and documents that the mapping
from Jai's text fixture IDs is still a team contract decision, so Week 1 does not make
that conversion silently.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AssignmentCreate(BaseModel):
    """Fields accepted from the browser when creating a consulting assignment."""

    problem: str
    department_id: str
    intended_result: str
    required_sections: list[str] = Field(min_length=1)
    audience: str
    constraints: list[str] = Field(default_factory=list)
    selected_document_version_ids: list[str] = Field(default_factory=list)
    request_type: Literal["problem", "RFP", "RFQ"] = "problem"

    @field_validator("problem", "department_id", "intended_result", "audience")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("required_sections")
    @classmethod
    def normalize_required_sections(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if not normalized:
            raise ValueError("must contain at least one requested section")
        return normalized

    @field_validator("constraints")
    @classmethod
    def normalize_constraints(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class AssignmentResponse(AssignmentCreate):
    """Normalized assignment returned by the application API."""

    assignment_id: str
    schema_version: Literal["1.0"] = "1.0"
    created_by: str


class ErrorField(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    fields: list[ErrorField] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody
