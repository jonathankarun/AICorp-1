# this file connects the web app to the database through API routes
# the demo token is for local testing and the server decides what sources are allowed
"""Authenticated local demo API. Real identity-provider integration is deferred."""

import hashlib
import os
import secrets
from contextlib import asynccontextmanager
from uuid import UUID
import psycopg
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from backend.data.db import connect, ROOT
from backend.data.models import AccessContext
from backend.data.week2_models import AssignmentInput, DocumentInput, SearchInput
from backend.data.workspace import (
    DataError,
    get_assignment,
    get_job,
    list_documents,
    list_jobs,
    save_assignment,
)
from backend.data.ingestion import process_job, submit_pdf
from backend.data.search import search
from backend.data.history import comparable_work, add_fact, resolve_chunk
from backend.data.week3_models import ComparableInput, FactInput
from backend.data.reports import save_report, get_report
from backend.engine.models import Report
from backend.data.operations import (CorrectionInput, RestrictionInput, ReviewInput,
    correct_payment, restrict_document, read_document, review_report)
from backend.data.demo import demo_spending


def create_app(
    connection_factory=connect,
    *,
    context=None,
    token=None,
    local_mode=None,
    max_bytes=None,
):
    enabled = (
        local_mode if local_mode is not None else os.getenv("AICORP_LOCAL_DEMO") == "1"
    )
    secret = token or os.getenv("AICORP_DEMO_TOKEN", "")
    max_bytes = max_bytes or int(os.getenv("AICORP_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
    trusted_context = context or AccessContext(
        actor_id=UUID("50000000-0000-4000-8000-000000000001"),
        allowed_department_ids=(UUID("10000000-0000-4000-8000-000000000001"),),
    )

    @asynccontextmanager
    async def lifespan(app):
        if not enabled or len(secret) < 16:
            raise RuntimeError(
                "Local API requires AICORP_LOCAL_DEMO=1 and AICORP_DEMO_TOKEN with at least 16 characters"
            )
        yield

    app = FastAPI(title="AI Corps Data Subsystem", version="4.0", lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )

    def identity(authorization: str | None = Header(default=None)):
        if (
            not enabled
            or len(secret) < 16
            or not secrets.compare_digest(authorization or "", "Bearer " + secret)
        ):
            raise DataError("unauthorized", 401)
        return trusted_context

    @app.exception_handler(DataError)
    async def domain_error(request, exc):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "fields": [".".join(map(str, e["loc"])) for e in exc.errors()],
                }
            },
        )

    @app.exception_handler(psycopg.Error)
    async def database_error(request, exc):
        return JSONResponse(
            status_code=503, content={"error": {"code": "database_unavailable"}}
        )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "mode": "local-fixture-demo"}

    @app.post("/api/v1/assignments", status_code=201)
    def create_assignment(data: AssignmentInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return save_assignment(conn, data, ctx)

    @app.get("/api/v1/assignments/{identifier}")
    def read_assignment(identifier: UUID, ctx=Depends(identity)):
        with connection_factory() as conn:
            return get_assignment(conn, identifier, ctx)

    @app.get("/api/v1/documents")
    def documents(ctx=Depends(identity)):
        with connection_factory() as conn:
            return list_documents(conn, ctx)

    @app.get("/api/v1/uploads")
    def jobs(ctx=Depends(identity)):
        with connection_factory() as conn:
            return list_jobs(conn, ctx)

    @app.get("/api/v1/uploads/{identifier}")
    def job(identifier: UUID, ctx=Depends(identity)):
        with connection_factory() as conn:
            return get_job(conn, identifier, ctx)

    def work(identifier):
        # Fresh connection commits processing then ready/failed. Unexpected DB
        # failures leave a durable job for the explicit recovery command.
        with connection_factory() as conn:
            process_job(conn, identifier)

    @app.post("/api/v1/documents", status_code=202)
    async def upload(
        background: BackgroundTasks,
        metadata: str = Form(...),
        file: UploadFile = File(...),
        ctx=Depends(identity),
    ):
        try:
            meta = DocumentInput.model_validate_json(metadata)
        except ValidationError:
            raise DataError("invalid_document_metadata", 422)
        content = await file.read(max_bytes + 1)
        await file.close()
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise DataError("pdf_required", 415)
        # Clients cannot grant external-model permission. Only the bundled,
        # fictional public PDF is allowlisted in this local demonstration.
        approved = ROOT / "tests/fixtures/week2/engagement.pdf"
        eligible = (
            approved.exists()
            and hashlib.sha256(content).digest()
            == hashlib.sha256(approved.read_bytes()).digest()
        )
        meta = meta.model_copy(
            update={
                "external_model_allowed": eligible and meta.access_status == "public"
            }
        )
        with connection_factory() as conn:
            identifier = submit_pdf(conn, content, meta, ctx, max_bytes)
            result = get_job(conn, identifier, ctx)
        background.add_task(work, identifier)
        return result

    @app.post("/api/v1/search")
    def find(data: SearchInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return search(conn, data, ctx)

    @app.post("/api/v1/comparables")
    def comparables(data: ComparableInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return comparable_work(conn, data, ctx)

    @app.post("/api/v1/facts", status_code=201)
    def fact(data: FactInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return {"fact_id": add_fact(conn, data, ctx)}

    @app.get("/api/v1/chunks/{identifier}")
    def chunk(identifier: UUID, ctx=Depends(identity)):
        with connection_factory() as conn:
            return resolve_chunk(conn, identifier, ctx)

    @app.get("/api/v1/documents/{identifier}/pdf")
    def pdf(identifier: UUID, ctx=Depends(identity)):
        with connection_factory() as conn:
            _, content = read_document(conn, identifier, ctx)
            return Response(content, media_type="application/pdf", headers={"Cache-Control": "no-store"})

    @app.post("/api/v1/documents/{identifier}/access")
    def access(identifier: UUID, data: RestrictionInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return restrict_document(conn, identifier, data, ctx)

    @app.get("/api/v1/demo/spending")
    def money(ctx=Depends(identity)):
        with connection_factory() as conn:
            return demo_spending(conn, ctx)

    @app.post("/api/v1/payments/{identifier}/classification")
    def correction(identifier: UUID, data: CorrectionInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return correct_payment(conn, identifier, data, ctx)

    @app.post("/api/v1/reports", status_code=201)
    def report(data: Report, ctx=Depends(identity)):
        with connection_factory() as conn:
            save_report(conn, data, ctx)
            return get_report(conn, UUID(data.report_id), data.version, ctx)

    @app.get("/api/v1/reports/{identifier}/{version}")
    def read_report(identifier: UUID, version: int, ctx=Depends(identity)):
        with connection_factory() as conn:
            return get_report(conn, identifier, version, ctx)

    @app.post("/api/v1/reports/{identifier}/{version}/reviews", status_code=201)
    def review(identifier: UUID, version: int, data: ReviewInput, ctx=Depends(identity)):
        with connection_factory() as conn:
            return review_report(conn, identifier, version, data, ctx)

    frontend = ROOT / "apps/web/dist"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="web")
    return app


app = create_app()
