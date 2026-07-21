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


def test_pipeline_returns_three_citations() -> None:
    passages = [
        Passage(passage_id="a", text="Insulin regulates blood glucose.", source="source-a"),
        Passage(passage_id="b", text="Insulin helps regulate glucose levels.", source="source-b"),
        Passage(passage_id="c", text="Blood glucose is regulated by insulin.", source="source-c"),
        Passage(passage_id="d", text="Paris is the capital of France.", source="source-d"),
    ]
    report = VerificationPipeline(passages).verify("Insulin regulates blood glucose.")
    verdict = report.verdicts[0]
    assert len(verdict.citations) == 3
    assert [item.citation_id for item in verdict.citations] == ["[1]", "[2]", "[3]"]


def test_pipeline_flags_conflicting_sources() -> None:
    passages = [
        Passage(passage_id="support", text="Aspirin increases bleeding risk."),
        Passage(passage_id="conflict", text="Aspirin does not increase bleeding risk."),
    ]
    report = VerificationPipeline(passages).verify("Aspirin increases bleeding risk.")
    verdict = report.verdicts[0]
    assert verdict.evidence_conflict
    assert verdict.nli.label is NLILabel.CONTRADICTION
    assert "conflicting_evidence" in verdict.review_reasons


def test_pipeline_abstains_without_relevant_evidence() -> None:
    passages = [Passage(passage_id="geo", text="Paris is the capital of France.")]
    report = VerificationPipeline(passages).verify("Quasars emit xylophonic radiation.")
    verdict = report.verdicts[0]
    assert verdict.nli.label is NLILabel.ABSTAIN
    assert verdict.nli.confidence == 1.0
    assert verdict.evidence is None
    assert verdict.citations == []
    assert "no_relevant_evidence" in verdict.review_reasons

