from dataclasses import dataclass

from verinli.models import NLILabel, NLIResult


@dataclass(frozen=True)
class AbstentionPolicy:
    min_nli_confidence: float = 0.67
    min_retrieval_score: float = 0.25

    def apply(self, result: NLIResult, retrieval_score: float) -> NLIResult:
        probabilities = self._normalize(result.probabilities)
        confident_nli = result.confidence >= self.min_nli_confidence
        relevant_evidence = retrieval_score >= self.min_retrieval_score
        if confident_nli and relevant_evidence:
            return result.model_copy(
                update={
                    "confidence": probabilities[result.label],
                    "probabilities": probabilities,
                }
            )

        abstention_probability = max(
            0.5,
            1.0 - result.confidence,
            1.0 - retrieval_score,
        )
        remaining_probability = 1.0 - abstention_probability
        non_abstain_total = sum(
            probability
            for label, probability in probabilities.items()
            if label is not NLILabel.ABSTAIN
        )
        calibrated = {
            label: (
                probability / non_abstain_total * remaining_probability
                if label is not NLILabel.ABSTAIN and non_abstain_total
                else 0.0
            )
            for label, probability in probabilities.items()
        }
        calibrated[NLILabel.ABSTAIN] = abstention_probability
        return NLIResult(
            label=NLILabel.ABSTAIN,
            confidence=abstention_probability,
            probabilities=calibrated,
            rationale=(
                f"Abstained: NLI confidence={result.confidence:.2f}, "
                f"retrieval score={retrieval_score:.2f}."
            ),
        )

    @staticmethod
    def no_evidence() -> NLIResult:
        return NLIResult(
            label=NLILabel.ABSTAIN,
            confidence=1.0,
            probabilities={label: float(label is NLILabel.ABSTAIN) for label in NLILabel},
            rationale="Abstained because no relevant evidence passage was retrieved.",
        )

    @staticmethod
    def _normalize(probabilities: dict[NLILabel, float]) -> dict[NLILabel, float]:
        complete = {label: max(0.0, probabilities.get(label, 0.0)) for label in NLILabel}
        total = sum(complete.values())
        if not total:
            return {label: 1.0 / len(NLILabel) for label in NLILabel}
        return {label: probability / total for label, probability in complete.items()}
