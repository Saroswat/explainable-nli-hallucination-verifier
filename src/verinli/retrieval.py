import math
import re
from collections import Counter
from dataclasses import dataclass

from verinli.models import Evidence


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass(frozen=True)
class Passage:
    passage_id: str
    text: str
    source: str | None = None


class LexicalRetriever:
    """Dependency-free BM25 retriever with an absolute relevance score."""

    k1 = 1.2
    b = 0.75

    def __init__(self, passages: list[Passage]) -> None:
        if not passages:
            raise ValueError("At least one evidence passage is required.")
        self.passages = passages
        self._docs = [Counter(_tokens(p.text)) for p in passages]
        self._doc_lengths = [sum(doc.values()) for doc in self._docs]
        self._average_doc_length = sum(self._doc_lengths) / len(self._doc_lengths)
        self._idf = self._build_idf()
        self._unseen_idf = math.log(1 + (len(self._docs) + 0.5) / 0.5)

    def _build_idf(self) -> dict[str, float]:
        count = Counter(token for doc in self._docs for token in doc)
        n = len(self._docs)
        return {
            token: math.log(1 + (n - document_frequency + 0.5) / (document_frequency + 0.5))
            for token, document_frequency in count.items()
        }

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        query_tokens = set(_tokens(query))
        normalizer = sum(self._idf.get(token, self._unseen_idf) for token in query_tokens)
        raw: list[tuple[float, Passage]] = []
        for passage, doc, document_length in zip(
            self.passages, self._docs, self._doc_lengths, strict=True
        ):
            length_factor = self.k1 * (
                1 - self.b + self.b * document_length / self._average_doc_length
            )
            score = 0.0
            for token in query_tokens:
                frequency = doc[token]
                if not frequency:
                    continue
                saturation = frequency * (self.k1 + 1) / (frequency + length_factor)
                score += self._idf[token] * saturation
            raw.append((score, passage))
        ranked = sorted(raw, key=lambda item: (-item[0], item[1].passage_id))[:top_k]
        return [
            Evidence(
                passage_id=p.passage_id,
                text=p.text,
                source=p.source,
                retrieval_score=min(score / normalizer, 1.0) if normalizer else 0.0,
            )
            for score, p in ranked
        ]

