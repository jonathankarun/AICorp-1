"""Run with python -m backend.data.cli from the repository root."""
import argparse
import json
import sys
from uuid import UUID

import psycopg
from pydantic import ValidationError

from .db import connect, migrate
from .models import AccessContext
from .repository import DataRepository
from .seed import seed


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Corps Week 1 local data tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate")
    sub.add_parser("seed")
    lookup = sub.add_parser("lookup")
    lookup.add_argument("engagement_id", type=UUID)
    lookup.add_argument("--actor-id", type=UUID, required=True)
    lookup.add_argument("--department-id", type=UUID, action="append", default=[])
    args = parser.parse_args()
    try:
        with connect() as conn:
            if args.command == "migrate":
                output = {"applied": migrate(conn)}
            elif args.command == "seed":
                output = {"inserted": seed(conn)}
            else:
                context = AccessContext(actor_id=args.actor_id, allowed_department_ids=tuple(args.department_id))
                result = DataRepository(conn).get_engagement(args.engagement_id, context)
                print(result.model_dump_json(indent=2))
                return 0 if result.result_type == "engagement" else 2
            print(json.dumps(output, indent=2))
        return 0
    except (ValueError, ValidationError) as exc:
        print(json.dumps({"code": "invalid_configuration_or_data", "message": str(exc)}), file=sys.stderr)
        return 1
    except psycopg.Error:
        # Driver errors may include connection details; keep the CLI response safe.
        print(json.dumps({"code": "database_error", "message": "Database operation failed; check configuration, service health, and migrations."}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

