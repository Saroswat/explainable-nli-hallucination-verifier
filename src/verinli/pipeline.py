from verinli.calibration import AbstentionPolicy
from verinli.claims import split_atomic_claims
from verinli.models import Citation, ClaimVerdict, GroundednessReport, NLILabel
from verinli.nli import HeuristicNLI, NLIBackend
from verinli.retrieval import LexicalRetriever, Passage


class VerificationPipeline:
    def __init__(
        self,
        passages: list[Passage],
        nli: NLIBackend | None = None,
        policy: AbstentionPolicy | None = None,
        top_k: int = 3,
    ) -> None:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        self.retriever = LexicalRetriever(passages)
        self.nli = nli or HeuristicNLI()
        self.policy = policy or AbstentionPolicy()
        self.top_k = top_k

    def verify(self, answer: str) -> GroundednessReport:
        verdicts: list[ClaimVerdict] = []
        for claim in split_atomic_claims(answer):
            evidence_candidates = [
                evidence
                for evidence in self.retriever.retrieve(claim, top_k=self.top_k)
                if evidence.retrieval_score >= self.policy.min_retrieval_score
            ]
            citations = [
                Citation(
                    citation_id=f"[{index}]",
                    evidence=evidence,
                    nli=self.policy.apply(
                        self.nli.predict(evidence.text, claim), evidence.retrieval_score
                    ),
                )
                for index, evidence in enumerate(evidence_candidates, start=1)
            ]

            if citations:
                contradictions = [
                    citation
                    for citation in citations
                    if citation.nli.label is NLILabel.CONTRADICTION
                ]
                primary = max(
                    contradictions or citations[:1],
                    key=lambda citation: (
                        citation.nli.confidence * citation.evidence.retrieval_score
                    ),
                )
                evidence = primary.evidence
                calibrated = primary.nli
            else:
                evidence = None
                calibrated = self.policy.no_evidence()

            citation_labels = {citation.nli.label for citation in citations}
            evidence_conflict = {
                NLILabel.ENTAILMENT,
                NLILabel.CONTRADICTION,
            }.issubset(citation_labels)
            reasons: list[str] = []
            if NLILabel.CONTRADICTION in citation_labels:
                reasons.append("contradiction")
            if calibrated.label is NLILabel.ABSTAIN:
                reasons.append("low_confidence")
            if not citations:
                reasons.append("no_relevant_evidence")
            if evidence_conflict:
                reasons.append("conflicting_evidence")
            verdicts.append(
                ClaimVerdict(
                    claim=claim,
                    evidence=evidence,
                    nli=calibrated,
                    citations=citations,
                    evidence_conflict=evidence_conflict,
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

