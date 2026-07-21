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

