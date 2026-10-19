# this file creates the data structures for comparable work and evidence-backed facts
# unknown outcomes stay empty, and contract amounts stay separate from payments
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .models import Contract


class FactInput(Contract):
    engagement_id: UUID
    kind: Literal[
        "specialty",
        "method",
        "deliverable",
        "recommendation",
        "outcome",
        "related_engagement",
        "contract_value",
    ]
    value: str | None = Field(default=None, min_length=1, max_length=10000)
    unknown_reason: str | None = Field(default=None, min_length=1, max_length=2000)
    evidence_chunk_id: UUID
    related_engagement_id: UUID | None = None
    amount: Decimal | None = Field(
        default=None, ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False
    )
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def check_fact(self):
        # this keeps an unknown result from looking like a successful outcome
        known = bool(self.value and self.value.strip()) and self.unknown_reason is None
        unknown = (
            self.kind == "outcome"
            and self.value is None
            and bool(self.unknown_reason and self.unknown_reason.strip())
        )
        if not (known or unknown):
            raise ValueError("Supply a value, or an unknown outcome with a reason")
        if (self.kind == "related_engagement") != (
            self.related_engagement_id is not None
        ):
            raise ValueError("Only related engagements need a related ID")
        if self.related_engagement_id == self.engagement_id:
            raise ValueError("An engagement cannot be related to itself")
        if self.kind == "contract_value":
            if self.amount is None or self.currency is None:
                raise ValueError("Contract value needs an amount and currency")
        elif self.amount is not None or self.currency is not None:
            raise ValueError("Only contract values have money fields")
        return self


class ComparableInput(Contract):
    topic: str | None = Field(default=None, min_length=1, max_length=300)
    department_id: UUID | None = None
    specialty: str | None = Field(default=None, min_length=1, max_length=300)
    for_external_model: bool = True
    limit: int = Field(default=10, ge=1, le=50)
