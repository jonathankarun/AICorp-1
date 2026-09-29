"""Regenerate the proposed repository schemas and examples without a database."""
import json
from uuid import UUID

from pydantic import TypeAdapter

from .db import ROOT
from .models import AccessContext, Department, Engagement, EngagementFound, EngagementNotFound, EngagementResult, Vendor
from .seed import load_fixture


def contract_files() -> dict:
    fixture = load_fixture()
    engagement = fixture["engagement"].copy()
    engagement.pop("vendor_id")
    engagement.pop("department_id")
    context = AccessContext(
        actor_id=UUID("50000000-0000-4000-8000-000000000001"),
        allowed_department_ids=(UUID(fixture["department"]["department_id"]),),
    )
    found = EngagementFound(engagement=Engagement(
        **engagement, vendor=Vendor(**fixture["vendor"]), department=Department(**fixture["department"])
    ))
    missing = EngagementNotFound(engagement_id=UUID("30000000-0000-4000-8000-000000000099"))
    return {
        "access-context.schema.json": AccessContext.model_json_schema(),
        "engagement-result.schema.json": TypeAdapter(EngagementResult).json_schema(),
        "access-context.example.json": context.model_dump(mode="json"),
        "engagement-found.example.json": found.model_dump(mode="json"),
        "engagement-not-found.example.json": missing.model_dump(mode="json"),
    }


if __name__ == "__main__":
    target = ROOT / "contracts/data/v1"
    target.mkdir(parents=True, exist_ok=True)
    for name, content in contract_files().items():
        (target / name).write_text(json.dumps(content, indent=2) + "\n")
        print(f"Wrote contracts/data/v1/{name}")
