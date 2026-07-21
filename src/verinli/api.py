from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from verinli.models import GroundednessReport
from verinli.pipeline import VerificationPipeline
from verinli.retrieval import Passage

app = FastAPI(
    title="VeriNLI",
    version="0.2.0",
    description="Explainable, evidence-grounded claim verification.",
)

_WEB_APP = Path(__file__).parent / "web" / "index.html"


class VerifyRequest(BaseModel):
    answer: str = Field(min_length=3, max_length=20_000)
    passages: list[Passage] = Field(min_length=1, max_length=500)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    """Serve the dependency-free local verification workbench."""
    return HTMLResponse(_WEB_APP.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/verify", response_model=GroundednessReport)
def verify(request: VerifyRequest) -> GroundednessReport:
    return VerificationPipeline(request.passages).verify(request.answer)

