from enum import StrEnum

from pydantic import BaseModel, Field


class NLILabel(StrEnum):
    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"
    ABSTAIN = "abstain"


class Evidence(BaseModel):
    passage_id: str
    text: str
    source: str | None = None
    retrieval_score: float = Field(ge=0.0, le=1.0)


class NLIResult(BaseModel):
    label: NLILabel
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[NLILabel, float]
    rationale: str


class ClaimVerdict(BaseModel):
    claim: str
    evidence: Evidence | None
    nli: NLIResult
    requires_human_review: bool
    review_reasons: list[str] = Field(default_factory=list)


class GroundednessReport(BaseModel):
    answer: str
    verdicts: list[ClaimVerdict]
    groundedness_score: float = Field(ge=0.0, le=1.0)
    contradiction_rate: float = Field(ge=0.0, le=1.0)
    review_required: bool
    summary: dict[str, int]

