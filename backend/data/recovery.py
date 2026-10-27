# this saves the whole database, including original PDFs and CSVs
# restore checks always use a new temporary database so our working copy stays safe
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from .db import connect, ROOT
from .testing import empty_test_database
from psycopg import sql


def inventory(conn):
    result = {}
    tables = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
    for row in tables:
        name = row['tablename']
        # sorted row text also catches changed money, source bytes, and missing citations
        rows = conn.execute(sql.SQL('SELECT row_to_json(t)::text AS value FROM {} t ORDER BY row_to_json(t)::text').format(sql.Identifier(name))).fetchall()
        payload = '\n'.join(r['value'] for r in rows).encode()
        result[name] = {'count': len(rows), 'sha256': hashlib.sha256(payload).hexdigest()}
    return result


def pg_tool(args, *, input=None):
    # these tools run inside our pinned local postgres container, so versions match
    command = ['docker', 'compose', 'exec', '-T', 'db', *args]
    return subprocess.run(command, cwd=ROOT, input=input, capture_output=True, check=True).stdout


def backup(directory: Path, database=None):
    directory.mkdir(parents=True, exist_ok=False)
    with connect(database) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        snapshot = conn.execute('SELECT pg_export_snapshot() AS snapshot').fetchone()['snapshot']
        details = inventory(conn)
        dump = pg_tool(['pg_dump', '-U', conn.info.user, '-d', conn.info.dbname,
                        '--format=custom', '--no-owner', '--snapshot=' + snapshot])
        manifest = {'database': conn.info.dbname, 'postgres': conn.info.server_version,
                    'tables': details, 'dump_sha256': hashlib.sha256(dump).hexdigest(),
                    'application_files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / 'backend').rglob('*.py'))},
                    'migrations': conn.execute('SELECT version,sha256 FROM schema_migrations ORDER BY version').fetchall()}
    (directory / 'database.dump').write_bytes(dump)
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def verify_restore(directory: Path):
    dump = (directory / 'database.dump').read_bytes()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if hashlib.sha256(dump).hexdigest() != manifest['dump_sha256']:
        raise ValueError('Backup checksum does not match')
    with empty_test_database() as conn:
        pg_tool(['pg_restore', '-U', conn.info.user, '-d', conn.info.dbname,
                 '--no-owner', '--exit-on-error'], input=dump)
        actual = inventory(conn)
        if actual != manifest['tables']:
            raise ValueError('Restored data does not match the snapshot')
        # postgres checks the foreign keys while restoring; the hashes check every saved row
        return {'passed': True, 'tables': len(actual), 'rows': sum(t['count'] for t in actual.values())}


def main():
    parser = argparse.ArgumentParser(description='Back up the local compose database or verify a backup in a disposable database')
    parser.add_argument('action', choices=['backup', 'verify'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = backup(args.directory) if args.action == 'backup' else verify_restore(args.directory)
    print(json.dumps(result, indent=2, default=str))

if __name__ == '__main__':
    main()
