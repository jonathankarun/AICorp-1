# this file finds past engagements and shows the evidence behind their details
# payment totals are calculated on their own so extra documents dont multiply the money
from uuid import uuid4
from .week3_models import FactInput, ComparableInput
from .workspace import DataError, list_documents


def require_engagement(conn, identifier, context):
    row = conn.execute(
        "SELECT * FROM engagements WHERE engagement_id=%s AND department_id=ANY(%s::uuid[])",
        (identifier, list(context.allowed_department_ids)),
    ).fetchone()
    if row is None:
        raise DataError("not_found", 404)
    return row


def resolve_chunk(conn, identifier, context, *, for_external_model=False):
    # this checks the exact saved version, never whichever version happens to be newest
    row = conn.execute(
        """SELECT c.*, v.title, v.source_uri, v.external_model_allowed, d.department_id
        FROM chunks c JOIN document_versions v USING(document_version_id)
        JOIN documents d USING(document_id)
        WHERE c.chunk_id=%s AND d.department_id=ANY(%s::uuid[])
          AND v.access_status<>'unknown' AND (NOT %s OR v.external_model_allowed)
          AND EXISTS(SELECT 1 FROM ingestion_jobs j WHERE j.document_version_id=v.document_version_id AND j.status='ready')""",
        (identifier, list(context.allowed_department_ids), for_external_model),
    ).fetchone()
    if row is None:
        raise DataError("source_not_ready_or_not_allowed", 422)
    return {**row, "locator": f"page {row['page_number']}"}


def link_document(conn, engagement_id, document_version_id, context):
    engagement = require_engagement(conn, engagement_id, context)
    source = next(
        (
            d
            for d in list_documents(conn, context)
            if d["document_version_id"] == document_version_id
        ),
        None,
    )
    if source is None or source["department_id"] != engagement["department_id"]:
        raise DataError("source_not_ready_or_not_allowed", 422)
    conn.execute(
        "INSERT INTO engagement_documents VALUES(%s,%s) ON CONFLICT DO NOTHING",
        (engagement_id, document_version_id),
    )


def add_fact(conn, data: FactInput, context):
    with conn.transaction():
        engagement = require_engagement(conn, data.engagement_id, context)
        evidence = resolve_chunk(conn, data.evidence_chunk_id, context)
        if evidence["department_id"] != engagement["department_id"]:
            raise DataError("source_not_ready_or_not_allowed", 422)
        if data.related_engagement_id:
            require_engagement(conn, data.related_engagement_id, context)
        identifier = uuid4()
        conn.execute(
            """INSERT INTO engagement_facts(fact_id,engagement_id,kind,value,unknown_reason,
            evidence_chunk_id,related_engagement_id,amount,currency) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                identifier,
                data.engagement_id,
                data.kind,
                data.value,
                data.unknown_reason,
                data.evidence_chunk_id,
                data.related_engagement_id,
                data.amount,
                data.currency,
            ),
        )
        link_document(
            conn, data.engagement_id, evidence["document_version_id"], context
        )
    return identifier


def comparable_work(conn, request: ComparableInput, context):
    # these are small-corpus queries; each engagement gets its own facts and money totals
    rows = conn.execute(
        """SELECT e.*, v.name AS vendor_name FROM engagements e JOIN vendors v USING(vendor_id)
        WHERE e.department_id=ANY(%s::uuid[]) AND (%s::uuid IS NULL OR e.department_id=%s)
        ORDER BY e.engagement_id""",
        (
            list(context.allowed_department_ids),
            request.department_id,
            request.department_id,
        ),
    ).fetchall()
    results = []
    for row in rows:
        documents = conn.execute(
            """SELECT v.* FROM engagement_documents ed JOIN document_versions v USING(document_version_id)
            JOIN documents d USING(document_id) WHERE ed.engagement_id=%s AND d.department_id=ANY(%s::uuid[])
            AND v.access_status<>'unknown' AND (NOT %s OR v.external_model_allowed)
            AND EXISTS(SELECT 1 FROM ingestion_jobs j WHERE j.document_version_id=v.document_version_id AND j.status='ready')
            ORDER BY v.document_version_id""",
            (
                row["engagement_id"],
                list(context.allowed_department_ids),
                request.for_external_model,
            ),
        ).fetchall()
        allowed = {d["document_version_id"] for d in documents}
        facts = conn.execute(
            """SELECT f.*, c.document_version_id, c.page_number FROM engagement_facts f
            JOIN chunks c ON c.chunk_id=f.evidence_chunk_id WHERE f.engagement_id=%s ORDER BY f.fact_id""",
            (row["engagement_id"],),
        ).fetchall()
        facts = [
            f
            for f in facts
            if f["document_version_id"] in allowed
            and (
                f["related_engagement_id"] is None
                or conn.execute(
                    "SELECT 1 FROM engagements WHERE engagement_id=%s AND department_id=ANY(%s::uuid[])",
                    (f["related_engagement_id"], list(context.allowed_department_ids)),
                ).fetchone()
            )
        ]
        reasons = []
        if request.department_id:
            reasons.append("same department")
        if request.specialty:
            if not any(
                f["kind"] == "specialty"
                and request.specialty.casefold() in (f["value"] or "").casefold()
                for f in facts
            ):
                continue
            reasons.append("specialty: " + request.specialty)
        if request.topic:
            texts = [row["title"]] + [f["value"] or "" for f in facts]
            if not any(request.topic.casefold() in t.casefold() for t in texts):
                continue
            reasons.append("topic: " + request.topic)
        # grouping only payments keeps two equal payments and avoids the many-to-many join trap
        payments = conn.execute(
            """SELECT currency, count(*) AS transaction_count, sum(amount) AS amount
            FROM payments WHERE engagement_id=%s GROUP BY currency ORDER BY currency""",
            (row["engagement_id"],),
        ).fetchall()
        results.append(
            {
                **row,
                "match_reasons": reasons
                or ["accessible engagement; no similarity filter supplied"],
                "documents": documents,
                "facts": facts,
                "payments": payments,
                "contract_values": [f for f in facts if f["kind"] == "contract_value"],
            }
        )
        if len(results) >= request.limit:
            break
    return results
