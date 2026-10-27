# this measures the same searches before and after adding the text index
# all the extra chunks are fictional and only exist in a temporary database
import hashlib
import json
import platform
import statistics
import time
from uuid import UUID, uuid4
from .db import ROOT, migrate
from .testing import empty_test_database
from .models import AccessContext
from .demo import prepare_demo, DOCUMENT, DEPARTMENT
from .search import search
from .week2_models import SearchInput

INDEX_SQL = "CREATE INDEX chunks_search_text ON chunks USING gin(to_tsvector('english',text))"

def measure(conn, context):
    timings, ids = [], []
    for i in range(30):
        query = ['timeline', 'specialpermit', 'missingterm'][i % 3]
        start = time.perf_counter()
        result = search(conn, SearchInput(query=query, for_external_model=False), context)
        timings.append((time.perf_counter() - start) * 1000)
        ids.append([str(c['chunk_id']) for c in result['chunks']])
    return {'milliseconds': timings, 'median_ms': statistics.median(timings),
            'p95_ms': sorted(timings)[28], 'returned_ids': ids}


def run():
    context = AccessContext(actor_id=UUID('50000000-0000-4000-8000-000000000001'), allowed_department_ids=(DEPARTMENT,))
    with empty_test_database() as conn:
        migrate(conn)
        start = time.perf_counter()
        prepare_demo(conn, context)
        import_ms = (time.perf_counter() - start) * 1000
        version = conn.execute('SELECT document_version_id FROM document_versions WHERE document_id=%s', (DOCUMENT,)).fetchone()['document_version_id']
        with conn.cursor() as cursor:
            cursor.executemany('INSERT INTO chunks VALUES(%s,%s,%s,%s,%s,%s)', [
                (uuid4(), version, i + 100, 1,
                 'Synthetic workload specialpermit' if i % 100 == 0 else 'Synthetic workload ordinary unrelated text',
                 hashlib.sha256(('synthetic-' + str(i)).encode()).hexdigest()) for i in range(10000)])
        # drop only in this disposable database so both phases use exactly the same rows
        conn.execute('DROP INDEX IF EXISTS chunks_search_text')
        conn.execute('ANALYZE')
        before = measure(conn, context)
        plan_before = conn.execute("EXPLAIN (ANALYZE, FORMAT JSON) SELECT chunk_id FROM chunks WHERE to_tsvector('english',text) @@ to_tsquery('english','specialpermit')").fetchone()
        conn.execute(INDEX_SQL)
        conn.execute('ANALYZE chunks')
        after = measure(conn, context)
        plan_after = conn.execute("EXPLAIN (ANALYZE, FORMAT JSON) SELECT chunk_id FROM chunks WHERE to_tsvector('english',text) @@ to_tsquery('english','specialpermit')").fetchone()
        assert before['returned_ids'] == after['returned_ids']
        counts = {name: conn.execute('SELECT count(*) AS n FROM ' + name).fetchone()['n'] for name in ['payments', 'documents', 'chunks']}
        return {'passed': True, 'dataset': 'fictional fixture plus 10000 synthetic chunks',
                'cache': 'warm/mixed; OS caches are not flushed; 30 sequential queries in each phase',
                'machine': platform.platform(), 'postgres': conn.info.server_version, 'counts': counts,
                'fixture_import_ms': import_ms,
                'database_bytes': conn.execute('SELECT pg_database_size(current_database()) AS n').fetchone()['n'],
                'before': before, 'after': after, 'plan_before': plan_before, 'plan_after': plan_after}

if __name__ == '__main__':
    result = run()
    path = ROOT / 'evidence/local/data-benchmark.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, default=str) + '\n')
    print(json.dumps({'passed': result['passed'], 'before_p95_ms': result['before']['p95_ms'], 'after_p95_ms': result['after']['p95_ms'], 'output': str(path)}))
