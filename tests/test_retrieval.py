import pytest

from verinli.retrieval import LexicalRetriever, Passage


def test_retriever_returns_relevant_passage() -> None:
    retriever = LexicalRetriever(
        [
            Passage(passage_id="a", text="Paris is the capital of France."),
            Passage(passage_id="b", text="Insulin regulates blood glucose."),
        ]
    )
    assert retriever.retrieve("What regulates blood glucose?", top_k=1)[0].passage_id == "b"


def test_retriever_requires_evidence() -> None:
    with pytest.raises(ValueError, match="At least one evidence passage"):
        LexicalRetriever([])


def test_relevance_is_absolute_instead_of_relative_to_the_best_weak_match() -> None:
    retriever = LexicalRetriever(
        [
            Passage(passage_id="exact", text="Insulin regulates blood glucose."),
            Passage(passage_id="weak", text="Insulin was discovered in the twentieth century."),
            Passage(passage_id="other", text="Paris is the capital of France."),
        ]
    )
    results = retriever.retrieve("Insulin regulates blood glucose.", top_k=3)
    scores = {item.passage_id: item.retrieval_score for item in results}
    assert scores["exact"] > 0.7
    assert scores["weak"] < 0.25


def test_retriever_returns_three_ranked_candidates() -> None:
    retriever = LexicalRetriever(
        [
            Passage(passage_id="a", text="Aspirin reduces pain."),
            Passage(passage_id="b", text="Aspirin may increase bleeding risk."),
            Passage(passage_id="c", text="Aspirin does not cure infections."),
            Passage(passage_id="d", text="Paris is in France."),
        ]
    )
    results = retriever.retrieve("Aspirin reduces pain and bleeding.", top_k=3)
    assert len(results) == 3
    assert [item.retrieval_score for item in results] == sorted(
        [item.retrieval_score for item in results], reverse=True
    )

