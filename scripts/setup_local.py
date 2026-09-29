"""Create a local Python environment, start PostgreSQL, migrate and seed.

Run from any directory with Python 3.12 or 3.13. Docker Desktop must be running.
Existing .env files and database volumes are preserved.
"""
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    if sys.version_info[:2] not in ((3, 12), (3, 13)):
        raise SystemExit("Use Python 3.12 or 3.13 for the tested dependency lock.")
    run("docker", "info", "--format", "Docker server: {{.ServerVersion}}")
    env_path = ROOT / ".env"
    if not env_path.exists():
        # Exclusive creation and owner-only permissions, including at creation time.
        fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write((ROOT / ".env.example").read_text().replace(
                "replace-with-a-local-password", secrets.token_hex(24)
            ))
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        run(sys.executable, "-m", "venv", str(ROOT / ".venv"))
    run(str(python), "-m", "pip", "install", "-r", "requirements.lock")
    run("docker", "compose", "up", "-d", "--wait", "db")
    run(str(python), "-m", "backend.data.cli", "migrate")
    run(str(python), "-m", "backend.data.cli", "seed")
    print("Local Week 1 database ready. Run .venv/bin/python -m backend.data.validate")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(f"Setup stopped: {exc}. See docs/week1/setup.md.")

