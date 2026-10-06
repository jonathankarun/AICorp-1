"""Export version 2 input schemas and the local API's OpenAPI contract."""

import json
from .db import ROOT
from .week2_models import AssignmentInput, DocumentInput, SearchInput


def artifacts():
    from backend.api.app import create_app

    return {
        **{
            name + ".schema.json": model.model_json_schema()
            for name, model in [
                ("assignment-input", AssignmentInput),
                ("document-input", DocumentInput),
                ("search-input", SearchInput),
            ]
        },
        "openapi.json": create_app().openapi(),
        "assignment.example.json": {
            "problem": "Improve permit intake",
            "department_id": "10000000-0000-4000-8000-000000000001",
            "intended_result": "Preliminary improvement plan",
            "audience": "Department leadership",
            "constraints": ["Six weeks"],
            "required_sections": ["findings", "recommendation"],
            "selected_document_version_ids": [],
            "request_type": "problem",
        },
    }


def main():
    directory = ROOT / "contracts/data/v2"
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in artifacts().items():
        (directory / name).write_text(json.dumps(value, indent=2) + "\n")


if __name__ == "__main__":
    main()
