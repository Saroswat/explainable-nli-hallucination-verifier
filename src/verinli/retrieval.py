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
    """Dependency-free BM25-like baseline, intentionally replaceable."""

    def __init__(self, passages: list[Passage]) -> None:
        if not passages:
            raise ValueError("At least one evidence passage is required.")
        self.passages = passages
        self._docs = [Counter(_tokens(p.text)) for p in passages]
        self._idf = self._build_idf()

    def _build_idf(self) -> dict[str, float]:
        count = Counter(token for doc in self._docs for token in doc)
        n = max(len(self._docs), 1)
        return {token: math.log((n + 1) / (df + 0.5)) + 1 for token, df in count.items()}

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        query_tokens = Counter(_tokens(query))
        raw: list[tuple[float, Passage]] = []
        for passage, doc in zip(self.passages, self._docs, strict=True):
            score = sum(min(freq, doc[token]) * self._idf.get(token, 0.0)
                        for token, freq in query_tokens.items())
            raw.append((score, passage))
        maximum = max((score for score, _ in raw), default=0.0)
        ranked = sorted(raw, key=lambda item: (-item[0], item[1].passage_id))[:top_k]
        return [
            Evidence(
                passage_id=p.passage_id,
                text=p.text,
                source=p.source,
                retrieval_score=(score / maximum if maximum else 0.0),
            )
            for score, p in ranked
        ]

