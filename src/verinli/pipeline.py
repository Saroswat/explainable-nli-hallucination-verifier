from verinli.calibration import AbstentionPolicy
from verinli.claims import split_atomic_claims
from verinli.models import ClaimVerdict, GroundednessReport, NLILabel
from verinli.nli import HeuristicNLI, NLIBackend
from verinli.retrieval import LexicalRetriever, Passage


class VerificationPipeline:
    def __init__(
        self,
        passages: list[Passage],
        nli: NLIBackend | None = None,
        policy: AbstentionPolicy | None = None,
    ) -> None:
        self.retriever = LexicalRetriever(passages)
        self.nli = nli or HeuristicNLI()
        self.policy = policy or AbstentionPolicy()

    def verify(self, answer: str) -> GroundednessReport:
        verdicts: list[ClaimVerdict] = []
        for claim in split_atomic_claims(answer):
            evidence = self.retriever.retrieve(claim, top_k=1)[0]
            raw = self.nli.predict(evidence.text, claim)
            calibrated = self.policy.apply(raw, evidence.retrieval_score)
            reasons = []
            if calibrated.label is NLILabel.CONTRADICTION:
                reasons.append("contradiction")
            if calibrated.label is NLILabel.ABSTAIN:
                reasons.append("low_confidence")
            verdicts.append(
                ClaimVerdict(
                    claim=claim,
                    evidence=evidence,
                    nli=calibrated,
                    requires_human_review=bool(reasons),
                    review_reasons=reasons,
                )
            )
        counts = {label.value: sum(v.nli.label is label for v in verdicts) for label in NLILabel}
        total = max(len(verdicts), 1)
        return GroundednessReport(
            answer=answer,
            verdicts=verdicts,
            groundedness_score=counts["entailment"] / total,
            contradiction_rate=counts["contradiction"] / total,
            review_required=any(v.requires_human_review for v in verdicts),
            summary=counts,
        )

