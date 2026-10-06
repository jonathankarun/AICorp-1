"""FastAPI entry point for Yasha's Week 1 application/integration subsystem."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import AssignmentCreate, AssignmentResponse
from .repository import InMemoryAssignmentRepository

app = FastAPI(
    title="AI Corps Application API",
    version="1.0.0-week1",
    description="Week 1 assignment workflow for the City consulting-tool prototype.",
)

# Local-only browser origin for the Vite development server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = InMemoryAssignmentRepository()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map FastAPI/Pydantic failures to the stable Week 1 frontend error shape."""
    fields = []
    for error in exc.errors():
        path = ".".join(str(part) for part in error["loc"] if part != "body") or "request"
        fields.append({"field": path, "message": error["msg"]})

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The assignment could not be created.",
                "fields": fields,
            }
        },
    )


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-corps-api", "week": "1"}


@app.post(
    "/api/v1/assignments",
    response_model=AssignmentResponse,
    status_code=201,
)
def create_assignment(payload: AssignmentCreate) -> AssignmentResponse:
    """Validate, normalize, assign a server ID, and store one assignment."""
    assignment = AssignmentResponse(
        **payload.model_dump(),
        assignment_id=str(uuid4()),
        schema_version="1.0",
        created_by="local-demo-user",
    )
    return repository.create(assignment)


@app.get("/api/v1/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: str) -> AssignmentResponse:
    assignment = repository.get(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="assignment not found")
    return assignment
