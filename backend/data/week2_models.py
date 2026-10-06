"""Strict input contracts shared by the data service and HTTP API."""

from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field, field_validator, model_validator
from .models import Contract


class AssignmentInput(Contract):
    problem: str = Field(min_length=1, max_length=10000)
    department_id: UUID
    intended_result: str = Field(min_length=1, max_length=3000)
    required_sections: list[str] = Field(default_factory=list)
    audience: str | None = None
    constraints: list[str] = Field(default_factory=list)
    selected_document_version_ids: list[UUID] = Field(
        default_factory=list, max_length=50
    )
    request_type: Literal["problem", "RFP", "RFQ"] = "problem"

    @field_validator("problem", "intended_result")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()


class DocumentInput(Contract):
    department_id: UUID
    title: str = Field(min_length=1, max_length=300)
    source_uri: str = Field(min_length=1, max_length=1000)
    issuer: str | None = None
    published_on: date | None = None
    access_status: Literal["public", "restricted", "unknown"] = "unknown"
    external_model_allowed: bool = False
    document_id: UUID | None = None

    @field_validator("title", "source_uri")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def unknown_is_not_approved(self):
        if self.access_status == "unknown" and self.external_model_allowed:
            raise ValueError("Unknown access cannot be approved for external models")
        return self


class SearchInput(Contract):
    query: str = Field(min_length=1, max_length=2000)
    selected_document_version_ids: list[UUID] | None = Field(
        default=None, max_length=50
    )
    limit: int = Field(default=5, ge=1, le=20)
    for_external_model: bool = True
