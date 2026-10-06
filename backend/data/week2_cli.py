"""Import a CSV plus source manifest into the configured local database."""

import argparse
import json
from pathlib import Path
from .db import connect, migrate
from .importer import import_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    importer = sub.add_parser("import-csv")
    importer.add_argument("csv", type=Path)
    importer.add_argument("manifest", type=Path)
    importer.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with connect() as conn:
        migrate(conn)
        result = import_csv(
            conn, args.csv.read_bytes(), json.loads(args.manifest.read_text())
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 2 if result["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
