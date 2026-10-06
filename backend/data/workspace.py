"""Persist assignments and expose only ready, authorized document versions."""

from uuid import uuid4
from psycopg.types.json import Jsonb
from .week2_models import AssignmentInput


class DataError(ValueError):
    def __init__(self, code, status=400):
        self.code, self.status = code, status
        super().__init__(code)


def require_department(context, department_id):
    if department_id not in context.allowed_department_ids:
        raise DataError("not_found", 404)


def list_documents(conn, context):
    return conn.execute(
        """
        SELECT v.*, d.department_id FROM document_versions v
        JOIN documents d USING(document_id)
        WHERE d.department_id = ANY(%s::uuid[]) AND v.access_status <> 'unknown'
        AND EXISTS (SELECT 1 FROM ingestion_jobs j
          WHERE j.document_version_id=v.document_version_id AND j.status='ready')
        ORDER BY v.title, v.version DESC
    """,
        (list(context.allowed_department_ids),),
    ).fetchall()


def save_assignment(conn, data: AssignmentInput, context):
    require_department(context, data.department_id)
    selected = set(data.selected_document_version_ids)
    allowed = {d["document_version_id"] for d in list_documents(conn, context)}
    if not selected <= allowed:
        raise DataError("source_not_ready_or_not_allowed", 422)
    identifier = uuid4()
    with conn.transaction():
        conn.execute(
            "INSERT INTO assignments(assignment_id,actor_id,department_id,payload) VALUES(%s,%s,%s,%s)",
            (
                identifier,
                context.actor_id,
                data.department_id,
                Jsonb(data.model_dump(mode="json")),
            ),
        )
        for source in selected:
            conn.execute(
                "INSERT INTO assignment_sources VALUES(%s,%s)", (identifier, source)
            )
    return get_assignment(conn, identifier, context)


def get_assignment(conn, identifier, context):
    row = conn.execute(
        """SELECT * FROM assignments WHERE assignment_id=%s
      AND actor_id=%s AND department_id=ANY(%s::uuid[])""",
        (identifier, context.actor_id, list(context.allowed_department_ids)),
    ).fetchone()
    if not row:
        raise DataError("not_found", 404)
    return {
        **row["payload"],
        "assignment_id": row["assignment_id"],
        "schema_version": "2.0",
        "created_at": row["created_at"],
    }


def list_jobs(conn, context):
    return conn.execute(
        """SELECT j.job_id,j.document_id,j.status,j.document_version_id,j.error_code,
      j.metadata->>'title' AS title, octet_length(j.raw_bytes) AS size_bytes
      FROM ingestion_jobs j JOIN documents d USING(document_id)
      WHERE d.department_id=ANY(%s::uuid[]) ORDER BY j.created_at DESC""",
        (list(context.allowed_department_ids),),
    ).fetchall()


def get_job(conn, job_id, context):
    result = next((j for j in list_jobs(conn, context) if j["job_id"] == job_id), None)
    if result is None:
        raise DataError("not_found", 404)
    return result
