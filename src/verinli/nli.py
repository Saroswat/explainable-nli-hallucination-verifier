import re
from typing import Protocol

from verinli.models import NLILabel, NLIResult


class NLIBackend(Protocol):
    def predict(self, premise: str, hypothesis: str) -> NLIResult: ...


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class HeuristicNLI:
    """Transparent offline baseline for tests and pipeline demonstrations."""

    negations = {"no", "not", "never", "without", "neither", "nor"}

    def predict(self, premise: str, hypothesis: str) -> NLIResult:
        p, h = _words(premise), _words(hypothesis)
        overlap = len(p & h) / max(len(h), 1)
        negation_conflict = bool(p & self.negations) != bool(h & self.negations)
        p_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", premise))
        h_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", hypothesis))
        number_conflict = bool(p_numbers and h_numbers and p_numbers != h_numbers)

        if (negation_conflict or number_conflict) and overlap >= 0.45:
            label, confidence = NLILabel.CONTRADICTION, min(0.95, 0.60 + overlap / 3)
            rationale = "Shared context contains conflicting negation or numerical values."
        elif overlap >= 0.72:
            label, confidence = NLILabel.ENTAILMENT, min(0.95, 0.55 + overlap / 2)
            rationale = "Most hypothesis terms are supported by the premise."
        else:
            label, confidence = NLILabel.NEUTRAL, max(0.51, 1 - overlap / 2)
            rationale = "The available premise does not establish or directly contradict the claim."
        remainder = (1 - confidence) / 2
        probabilities: dict[NLILabel, float] = {
            item: remainder for item in NLILabel if item is not NLILabel.ABSTAIN
        }
        probabilities[label] = confidence
        probabilities[NLILabel.ABSTAIN] = 0.0
        return NLIResult(
            label=label,
            confidence=confidence,
            probabilities=probabilities,
            rationale=rationale,
        )


class TransformersNLI:
    """Optional Hugging Face sequence-classification backend."""

    def __init__(self, model_name: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli") -> None:
        from transformers import pipeline

        self._classifier = pipeline("text-classification", model=model_name, top_k=None)

    def predict(self, premise: str, hypothesis: str) -> NLIResult:
        scores = self._classifier({"text": premise, "text_pair": hypothesis})[0]
        mapped = {
            NLILabel(item["label"].lower()): float(item["score"])
            for item in scores
            if item["label"].lower() in {x.value for x in NLILabel}
        }
        label = max(mapped, key=lambda item: mapped[item])
        return NLIResult(
            label=label,
            confidence=mapped[label],
            probabilities=mapped,
            rationale="Prediction from a pretrained cross-encoder NLI model.",
        )
