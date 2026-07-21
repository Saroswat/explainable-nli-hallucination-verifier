from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from verinli.ingestion import passages_from_text
from verinli.models import GroundednessReport
from verinli.pipeline import VerificationPipeline
from verinli.reporting import report_to_csv
from verinli.retrieval import Passage

app = FastAPI(
    title="VeriNLI",
    version="0.3.0",
    description="Explainable, evidence-grounded claim verification.",
)

_WEB_APP = Path(__file__).parent / "web" / "index.html"


class VerifyRequest(BaseModel):
    answer: str = Field(min_length=3, max_length=20_000)
    passages: list[Passage] = Field(min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    source: str = Field(default="plain-text", min_length=1, max_length=200)
    max_characters: int = Field(default=800, ge=100, le=5_000)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    """Serve the dependency-free local verification workbench."""
    return HTMLResponse(_WEB_APP.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/verify", response_model=GroundednessReport)
def verify(request: VerifyRequest) -> GroundednessReport:
    return VerificationPipeline(request.passages, top_k=request.top_k).verify(request.answer)


@app.post("/verify.csv", response_class=PlainTextResponse)
def verify_csv(request: VerifyRequest) -> PlainTextResponse:
    report = VerificationPipeline(request.passages, top_k=request.top_k).verify(request.answer)
    return PlainTextResponse(
        report_to_csv(report),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="verinli-report.csv"'},
    )


@app.post("/ingest", response_model=list[Passage])
def ingest(request: IngestRequest) -> list[Passage]:
    return passages_from_text(request.text, request.source, request.max_characters)

