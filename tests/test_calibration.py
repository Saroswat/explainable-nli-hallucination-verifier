import pytest

from verinli.calibration import AbstentionPolicy
from verinli.models import NLILabel, NLIResult


def _result(confidence: float = 0.8) -> NLIResult:
    remainder = (1 - confidence) / 2
    return NLIResult(
        label=NLILabel.ENTAILMENT,
        confidence=confidence,
        probabilities={
            NLILabel.ENTAILMENT: confidence,
            NLILabel.CONTRADICTION: remainder,
            NLILabel.NEUTRAL: remainder,
            NLILabel.ABSTAIN: 0.0,
        },
        rationale="test result",
    )


def test_abstention_probabilities_are_normalized() -> None:
    result = AbstentionPolicy().apply(_result(), retrieval_score=0.1)
    assert result.label is NLILabel.ABSTAIN
    assert result.confidence == pytest.approx(0.9)
    assert sum(result.probabilities.values()) == pytest.approx(1.0)
    assert result.probabilities[NLILabel.ABSTAIN] == result.confidence


def test_confident_result_remains_normalized() -> None:
    result = AbstentionPolicy().apply(_result(), retrieval_score=0.8)
    assert result.label is NLILabel.ENTAILMENT
    assert sum(result.probabilities.values()) == pytest.approx(1.0)


def test_no_evidence_is_a_confident_abstention() -> None:
    result = AbstentionPolicy.no_evidence()
    assert result.label is NLILabel.ABSTAIN
    assert result.confidence == 1.0
    assert sum(result.probabilities.values()) == 1.0
