"""Proposed Week 1 repository contract, separate from the existing engine schema."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccessContext(Contract):
    # Supplied by the trusted server. CLI test identities are not authentication.
    actor_id: UUID
    allowed_department_ids: tuple[UUID, ...] = ()


class Vendor(Contract):
    vendor_id: UUID
    source_key: str
    name: str
    source_uri: str


class Department(Contract):
    department_id: UUID
    source_key: str
    name: str
    source_uri: str


class Engagement(Contract):
    engagement_id: UUID
    source_key: str
    title: str
    source_uri: str
    vendor: Vendor
    department: Department


class EngagementFound(Contract):
    result_type: Literal["engagement"] = "engagement"
    schema_version: Literal["1.0"] = "1.0"
    engagement: Engagement


class EngagementNotFound(Contract):
    result_type: Literal["not_found"] = "not_found"
    schema_version: Literal["1.0"] = "1.0"
    engagement_id: UUID
    code: Literal["engagement_not_found"] = "engagement_not_found"
    message: str = "Engagement not found or not accessible."


EngagementResult = EngagementFound | EngagementNotFound

