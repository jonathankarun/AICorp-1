# this file saves report versions and their citations together
# old reports keep their original chunks even after someone uploads a newer PDF
from uuid import UUID, uuid4
from psycopg.types.json import Jsonb
from backend.engine.models import Report
from .history import resolve_chunk
from .workspace import DataError, get_assignment


def save_report(conn, report: Report, context):
    # the engine keeps string IDs for mocks; real storage needs real UUIDs
    report = Report.model_validate(report.model_dump())
    report_id, assignment_id = UUID(report.report_id), UUID(report.assignment_id)
    if report.version < 1 or not report.sections:
        raise DataError("invalid_report", 422)
    ids = [c.citation_id for c in report.citations]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise DataError("invalid_citation_ids", 422)
    with conn.transaction():
        assignment = get_assignment(conn, assignment_id, context)
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(report_id),)
        )
        existing = conn.execute(
            "SELECT * FROM reports WHERE report_id=%s", (report_id,)
        ).fetchone()
        if existing and (
            existing["assignment_id"] != assignment_id
            or existing["actor_id"] != context.actor_id
        ):
            raise DataError("not_found", 404)
        latest = conn.execute(
            "SELECT coalesce(max(version),0) AS version FROM report_versions WHERE report_id=%s",
            (report_id,),
        ).fetchone()["version"]
        if report.version != latest + 1:
            raise DataError("report_version_conflict", 409)
        sources = []
        for citation in report.citations:
            source = resolve_chunk(conn, UUID(citation.evidence_chunk_id), context)
            if str(source["department_id"]) != str(assignment["department_id"]):
                raise DataError("source_not_ready_or_not_allowed", 422)
            selected = assignment["selected_document_version_ids"]
            if selected and str(source["document_version_id"]) not in selected:
                raise DataError("citation_outside_assignment", 422)
            sources.append((citation.citation_id, source))
        if not existing:
            conn.execute(
                "INSERT INTO reports VALUES(%s,%s,%s)",
                (report_id, assignment_id, context.actor_id),
            )
        identifier = uuid4()
        conn.execute(
            "INSERT INTO report_versions(report_version_id,report_id,version,content) VALUES(%s,%s,%s,%s)",
            (
                identifier,
                report_id,
                report.version,
                Jsonb(report.model_dump(mode="json")),
            ),
        )
        for citation_id, source in sources:
            conn.execute(
                "INSERT INTO report_citations VALUES(%s,%s,%s,%s)",
                (
                    identifier,
                    citation_id,
                    source["chunk_id"],
                    source["document_version_id"],
                ),
            )
    return identifier


def get_report(conn, report_id, version, context):
    row = conn.execute(
        """SELECT rv.* FROM report_versions rv JOIN reports r USING(report_id)
        JOIN assignments a USING(assignment_id) WHERE r.report_id=%s AND rv.version=%s
        AND r.actor_id=%s AND a.department_id=ANY(%s::uuid[])""",
        (report_id, version, context.actor_id, list(context.allowed_department_ids)),
    ).fetchone()
    if row is None:
        raise DataError("not_found", 404)
    citations = conn.execute(
        "SELECT * FROM report_citations WHERE report_version_id=%s ORDER BY citation_id",
        (row["report_version_id"],),
    ).fetchall()
    # check access again when reading, since callers can lose department access
    return {
        **row,
        "citations": [
            {**c, "source": resolve_chunk(conn, c["chunk_id"], context)}
            for c in citations
        ],
    }
