"""Durable PDF intake; page-bounded chunks and immutable evidence versions."""

import hashlib
from io import BytesIO
from uuid import uuid4, uuid5
from pypdf import PdfReader
from psycopg.types.json import Jsonb
from .week2_models import DocumentInput
from .workspace import DataError, require_department

EXTRACTION_VERSION = "pypdf-page-paragraph-v1"
MAX_PAGES = 100
CHUNK_CHARS = 1200
MAX_TEXT_CHARS = 500_000


def digest(content):
    return hashlib.sha256(content).hexdigest()


def submit_pdf(
    conn, content: bytes, metadata: DocumentInput, context, max_bytes=10 * 1024 * 1024
):
    require_department(context, metadata.department_id)
    if len(content) > max_bytes:
        raise DataError("file_too_large", 413)
    if not content.startswith(b"%PDF-"):
        raise DataError("pdf_required", 415)
    document_id = metadata.document_id or uuid4()
    with conn.transaction():
        if metadata.document_id:
            found = conn.execute(
                "SELECT * FROM documents WHERE document_id=%s", (document_id,)
            ).fetchone()
            if (
                not found
                or found["department_id"] != metadata.department_id
                or found["actor_id"] != context.actor_id
            ):
                raise DataError("not_found", 404)
        else:
            conn.execute(
                "INSERT INTO documents VALUES(%s,%s,%s)",
                (document_id, metadata.department_id, context.actor_id),
            )
        job_id = uuid4()
        conn.execute(
            """INSERT INTO ingestion_jobs(job_id,document_id,status,metadata,raw_bytes,content_hash)
          VALUES(%s,%s,'pending',%s,%s,%s)""",
            (
                job_id,
                document_id,
                Jsonb(metadata.model_dump(mode="json")),
                content,
                digest(content),
            ),
        )
    return job_id


def extract_chunks(content):
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted or len(reader.pages) > MAX_PAGES:
            raise DataError("pdf_encrypted_or_too_many_pages")
        chunks, total = [], 0
        for page_number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            # Partial extraction is also a review case: don't hide scanned pages.
            if not text:
                raise DataError("empty_or_scanned_page")
            total += len(text)
            if total > MAX_TEXT_CHARS:
                raise DataError("extracted_text_too_large")
            for paragraph in text.split("\n\n"):
                paragraph = paragraph.strip()
                while paragraph:
                    cut = min(CHUNK_CHARS, len(paragraph))
                    if cut < len(paragraph):
                        space = paragraph.rfind(" ", 0, cut)
                        if space > 0:
                            cut = space
                    part, paragraph = paragraph[:cut].strip(), paragraph[cut:].strip()
                    if part:
                        chunks.append((page_number, part))
        if not chunks:
            raise DataError("empty_or_scanned_page")
        return chunks
    except DataError:
        raise
    except Exception as exc:
        raise DataError("unreadable_pdf") from exc


def process_job(conn, job_id):
    """Caller commits submission first. Lock each document to serialize versions.

    Processing and ready are committed separately by the worker connection.
    An interrupted processing job can be explicitly resumed with the same ID.
    """
    with conn.transaction():
        job = conn.execute(
            "SELECT * FROM ingestion_jobs WHERE job_id=%s FOR UPDATE", (job_id,)
        ).fetchone()
        if not job:
            raise DataError("not_found", 404)
        if job["status"] in ("ready", "failed"):
            return job["status"]
        conn.execute(
            "UPDATE ingestion_jobs SET status='processing' WHERE job_id=%s", (job_id,)
        )
    try:
        chunks = extract_chunks(bytes(job["raw_bytes"]))
    except DataError as exc:
        with conn.transaction():
            conn.execute(
                "UPDATE ingestion_jobs SET status='failed',error_code=%s WHERE job_id=%s AND status<>'ready'",
                (exc.code, job_id),
            )
        return "failed"
    with conn.transaction():
        # Serializes different jobs for the same document and duplicate workers.
        conn.execute(
            "SELECT document_id FROM documents WHERE document_id=%s FOR UPDATE",
            (job["document_id"],),
        )
        current = conn.execute(
            "SELECT status FROM ingestion_jobs WHERE job_id=%s FOR UPDATE", (job_id,)
        ).fetchone()
        if current["status"] == "ready":
            return "ready"
        meta = job["metadata"]
        previous = conn.execute(
            """SELECT v.*,j.metadata FROM document_versions v
          JOIN ingestion_jobs j USING(document_version_id)
          WHERE v.document_id=%s AND j.status='ready' ORDER BY v.version DESC LIMIT 1""",
            (job["document_id"],),
        ).fetchone()
        # Unchanged content AND metadata reuse the immutable version.
        if (
            previous
            and previous["content_hash"] == job["content_hash"]
            and previous["extraction_version"] == EXTRACTION_VERSION
            and {k: v for k, v in previous["metadata"].items() if k != "document_id"}
            == {k: v for k, v in meta.items() if k != "document_id"}
        ):
            version_id = previous["document_version_id"]
        else:
            version = (previous["version"] + 1) if previous else 1
            version_id = uuid5(
                job["document_id"],
                f"{version}:{job['content_hash']}:{EXTRACTION_VERSION}",
            )
            conn.execute(
                """INSERT INTO document_versions(document_version_id,document_id,version,title,
              issuer,published_on,source_uri,content_hash,extraction_version,access_status,external_model_allowed)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    version_id,
                    job["document_id"],
                    version,
                    meta["title"],
                    meta["issuer"],
                    meta["published_on"],
                    meta["source_uri"],
                    job["content_hash"],
                    EXTRACTION_VERSION,
                    meta["access_status"],
                    meta["external_model_allowed"],
                ),
            )
            for ordinal, (page, text) in enumerate(chunks):
                conn.execute(
                    "INSERT INTO chunks VALUES(%s,%s,%s,%s,%s,%s)",
                    (
                        uuid5(version_id, str(ordinal)),
                        version_id,
                        ordinal,
                        page,
                        text,
                        digest(text.encode()),
                    ),
                )
        conn.execute(
            "UPDATE ingestion_jobs SET status='ready',document_version_id=%s,error_code=NULL WHERE job_id=%s",
            (version_id, job_id),
        )
    return "ready"
