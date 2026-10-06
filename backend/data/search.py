"""Measured keyword baseline; all eligibility filters run before ranking."""

import re
from uuid import uuid4
from psycopg.types.json import Jsonb
from .week2_models import SearchInput


def search(conn, request: SearchInput, context):
    # OR semantics helps multi-field assignment queries; lexemes are parameterized.
    terms = sorted(set(re.findall(r"[\w]+", request.query.lower())))
    tsquery = " | ".join(terms)
    rows = []
    if terms:
        rows = conn.execute(
            """
          SELECT c.chunk_id,c.document_version_id,c.text,c.page_number,c.content_hash,
            v.title,v.source_uri,v.access_status,v.external_model_allowed,
            ts_rank_cd(to_tsvector('english',c.text),to_tsquery('english',%s)) AS score
          FROM chunks c JOIN document_versions v USING(document_version_id)
          JOIN documents d USING(document_id)
          WHERE d.department_id=ANY(%s::uuid[]) AND v.access_status<>'unknown'
            AND (NOT %s OR v.external_model_allowed)
            AND (%s::uuid[] IS NULL OR v.document_version_id=ANY(%s::uuid[]))
            AND EXISTS(SELECT 1 FROM ingestion_jobs j WHERE j.document_version_id=v.document_version_id AND j.status='ready')
            AND to_tsvector('english',c.text) @@ to_tsquery('english',%s)
          ORDER BY score DESC,c.chunk_id LIMIT %s
        """,
            (
                tsquery,
                list(context.allowed_department_ids),
                request.for_external_model,
                request.selected_document_version_ids,
                request.selected_document_version_ids,
                tsquery,
                request.limit,
            ),
        ).fetchall()
    for row in rows:
        row["locator"] = f"page {row['page_number']}"
    identifier = uuid4()
    conn.execute(
        "INSERT INTO search_runs(search_id,actor_id,query,filters,returned_ids) VALUES(%s,%s,%s,%s,%s)",
        (
            identifier,
            context.actor_id,
            request.query,
            Jsonb(request.model_dump(mode="json")),
            Jsonb([str(r["chunk_id"]) for r in rows]),
        ),
    )
    return {
        "search_id": identifier,
        "result_type": "evidence" if rows else "evidence_gap",
        "chunks": rows,
    }
