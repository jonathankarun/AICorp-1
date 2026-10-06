"""Run real-browser checks against a disposable, freshly migrated database."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.data.testing import empty_test_database
from backend.data.db import migrate
from backend.data.seed import seed


def main():
    with empty_test_database() as conn:
        migrate(conn)
        seed(conn)
        conn.commit()
        env = {
            **os.environ,
            "POSTGRES_DB": conn.info.dbname,
            "AICORP_LOCAL_DEMO": "1",
            "AICORP_PYTHON": sys.executable,
            "AICORP_DEMO_TOKEN": "week2-browser-fixture-token",
        }
        result = subprocess.run(
            ["npm", "test", "--prefix", "apps/web"], cwd=ROOT, env=env
        )
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
