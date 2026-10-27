# this runs the acceptance checks and saves the output so someone else can repeat them
# the database tests create their own temporary databases, never reset the working one
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description='Validate the data subsystem using disposable databases')
    parser.add_argument('--disposable', action='store_true', required=True, help='Acknowledge that the checks create and remove temporary test databases')
    parser.add_argument('--browser', action='store_true', help='Also build the UI and run browser checks')
    args = parser.parse_args()
    target = ROOT / 'evidence/local'
    target.mkdir(parents=True, exist_ok=True)
    commands = [('data-acceptance.txt', [sys.executable, '-m', 'pytest', '--run-data', '-q', '--tb=short'])]
    if args.browser:
        commands += [('data-build.txt', ['npm', 'run', 'build', '--prefix', 'apps/web']),
                     ('data-browser.txt', [sys.executable, 'scripts/test_week2_browser.py'])]
    for name, command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (target / name).write_text(result.stdout)
        print(result.stdout, flush=True)
        if result.returncode:
            return result.returncode
    print('PASS: all requested checks completed. Evidence is in evidence/local/.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
