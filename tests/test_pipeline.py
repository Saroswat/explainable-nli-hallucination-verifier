from verinli.claims import split_atomic_claims
from verinli.models import NLILabel
from verinli.nli import HeuristicNLI
from verinli.pipeline import VerificationPipeline
from verinli.retrieval import Passage


def test_atomic_claim_split_handles_contrast() -> None:
    text = "Aspirin reduces pain, but it does not cure infections. It may increase bleeding."
    assert split_atomic_claims(text) == [
        "Aspirin reduces pain",
        "it does not cure infections",
        "It may increase bleeding",
    ]


def test_numerical_substitution_is_contradiction() -> None:
    result = HeuristicNLI().predict(
        "The trial enrolled 120 patients and lasted 12 weeks.",
        "The trial enrolled 220 patients and lasted 12 weeks.",
    )
    assert result.label is NLILabel.CONTRADICTION


def test_negation_attack_is_contradiction() -> None:
    result = HeuristicNLI().predict(
        "Metformin is recommended for adults with type 2 diabetes.",
        "Metformin is not recommended for adults with type 2 diabetes.",
    )
    assert result.label is NLILabel.CONTRADICTION


def test_pipeline_routes_contradiction_to_review() -> None:
    passages = [
        Passage(
            passage_id="bio-1",
            text="BRCA1 pathogenic variants increase breast cancer risk.",
            source="example-guideline",
        )
    ]
    report = VerificationPipeline(passages).verify(
        "BRCA1 pathogenic variants do not increase breast cancer risk."
    )
    assert report.review_required
    assert report.verdicts[0].review_reasons == ["contradiction"]

