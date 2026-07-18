from dataclasses import dataclass

from verinli.models import NLILabel, NLIResult


@dataclass(frozen=True)
class AbstentionPolicy:
    min_nli_confidence: float = 0.67
    min_retrieval_score: float = 0.25

    def apply(self, result: NLIResult, retrieval_score: float) -> NLIResult:
        confident_nli = result.confidence >= self.min_nli_confidence
        relevant_evidence = retrieval_score >= self.min_retrieval_score
        if confident_nli and relevant_evidence:
            return result
        return NLIResult(
            label=NLILabel.ABSTAIN,
            confidence=max(0.0, 1.0 - result.confidence),
            probabilities={**result.probabilities, NLILabel.ABSTAIN: 1.0 - result.confidence},
            rationale=(
                f"Abstained: NLI confidence={result.confidence:.2f}, "
                f"retrieval score={retrieval_score:.2f}."
            ),
        )
