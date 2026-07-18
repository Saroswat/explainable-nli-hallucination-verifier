from fastapi import FastAPI
from pydantic import BaseModel

from verinli.models import GroundednessReport
from verinli.pipeline import VerificationPipeline
from verinli.retrieval import Passage

app = FastAPI(title="VeriNLI", version="0.1.0")


class VerifyRequest(BaseModel):
    answer: str
    passages: list[Passage]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/verify", response_model=GroundednessReport)
def verify(request: VerifyRequest) -> GroundednessReport:
    return VerificationPipeline(request.passages).verify(request.answer)

