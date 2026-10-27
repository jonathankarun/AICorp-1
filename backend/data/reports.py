# this file saves report versions and their citations together
# old reports keep their original chunks even after someone uploads a newer PDF
from uuid import UUID, uuid4
from psycopg.types.json import Jsonb
from backend.engine.models import Report
from .history import resolve_chunk
from .workspace import DataError, get_assignment


def save_report(conn, report: Report, context):
    # save a new report version and all its citations as one operation
    # recheck the report in case something was changed after it was first created
    # the engine keeps string IDs for mocks; real storage needs real UUIDs
    report = Report.model_validate(report.model_dump())
    try:
        report_id, assignment_id = UUID(report.report_id), UUID(report.assignment_id)
        for citation in report.citations:
            UUID(citation.evidence_chunk_id)
    except (ValueError, TypeError, AttributeError):
        raise DataError("invalid_report_identifier", 422)
    if report.status != "draft":
        raise DataError("new_report_must_be_draft", 422)
    if report.version < 1 or not report.sections:
        raise DataError("invalid_report", 422)
    # citation labels need to be filled in and cant repeat within the report
    ids = [c.citation_id for c in report.citations]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise DataError("invalid_citation_ids", 422)
    # if anything below fails, undo the writes from this save
    with conn.transaction():
        # make sure this user can access the assignment the report belongs to
        assignment = get_assignment(conn, assignment_id, context)
        # only let one writer save this report at a time so they cant claim the same version
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(report_id),)
        )
        existing = conn.execute(
            "SELECT * FROM reports WHERE report_id=%s", (report_id,)
        ).fetchone()
        # an existing report has to stay with the same assignment and owner
        if existing and (
            existing["assignment_id"] != assignment_id
            or existing["actor_id"] != context.actor_id
        ):
            raise DataError("not_found", 404)
        # versions go 1, 2, 3, etc, so duplicates and skipped numbers get rejected
        latest = conn.execute(
            "SELECT coalesce(max(version),0) AS version FROM report_versions WHERE report_id=%s",
            (report_id,),
        ).fetchone()["version"]
        if report.version != latest + 1:
            raise DataError("report_version_conflict", 409)
        # check every citation before we start inserting the report
        sources = []
        for citation in report.citations:
            source = resolve_chunk(conn, UUID(citation.evidence_chunk_id), context)
            if str(source["department_id"]) != str(assignment["department_id"]):
                raise DataError("source_not_ready_or_not_allowed", 422)
            # if the assignment has selected documents, only those exact versions can be cited
            selected = assignment["selected_document_version_ids"]
            if selected and str(source["document_version_id"]) not in selected:
                raise DataError("citation_outside_assignment", 422)
            sources.append((citation.citation_id, source))
        if not existing:
            # a brand new report needs a row connecting its ID to the assignment and owner
            conn.execute(
                "INSERT INTO reports VALUES(%s,%s,%s)",
                (report_id, assignment_id, context.actor_id),
            )
        # this version gets its own ID, and we store the report content as JSON
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
        # save each citation with the exact chunk and document version it came from
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
    # pull up the version we asked for, but only for its owner with department access
    row = conn.execute(
        """SELECT rv.* FROM report_versions rv JOIN reports r USING(report_id)
        JOIN assignments a USING(assignment_id) WHERE r.report_id=%s AND rv.version=%s
        AND r.actor_id=%s AND a.department_id=ANY(%s::uuid[])""",
        (report_id, version, context.actor_id, list(context.allowed_department_ids)),
    ).fetchone()
    if row is None:
        raise DataError("not_found", 404)
    # get the citations saved with this particular report version
    citations = conn.execute(
        "SELECT * FROM report_citations WHERE report_version_id=%s ORDER BY citation_id",
        (row["report_version_id"],),
    ).fetchall()
    # check access again when reading, since callers can lose department access
    # return the report with the actual source text and details attached to each citation
    return {
        **row,
        "reviews": conn.execute("SELECT * FROM report_reviews WHERE report_version_id=%s ORDER BY revision", (row["report_version_id"],)).fetchall(),
        "citations": [
            {**c, "source": resolve_chunk(conn, c["chunk_id"], context)}
            for c in citations
        ],
    }
